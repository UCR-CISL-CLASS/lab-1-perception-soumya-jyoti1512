import glob
import os
import sys
try:
    sys.path.append(glob.glob
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla

import random
import time
import numpy as np
import cv2

IM_WIDTH = 640
IM_HEIGHT = 480


def process_img(image):
    # Convert raw image data to an OpenCV format (RGB)
    i = np.array(image.raw_data)
    i2 = i.reshape((IM_HEIGHT, IM_WIDTH, 4))
    i3 = i2[:, :, :3]
    i3 = cv2.cvtColor(i3, cv2.COLOR_RGB2BGR)

    # Get the list of objects in the scene (vehicles, pedestrians, etc.)
    world = image.frame

    # Loop through the actors (vehicles, pedestrians, etc.)
    for actor in world.get_actors():
        if actor.type_id.startswith('vehicle'):
            # Get the bounding box for the vehicle
            transform = actor.get_transform()
            location = transform.location

            # Project the 3D bounding box to the 2D image plane
            bbox = actor.bounding_box
            # Extract coordinates
            top_left = (int(location.x - bbox.extent.x), int(location.y - bbox.extent.y))
            bottom_right = (int(location.x + bbox.extent.x), int(location.y + bbox.extent.y))

            # Draw a bounding box around the vehicle
            cv2.rectangle(i3, top_left, bottom_right, (0, 255, 0), 2)

    # Display the image with bounding boxes
    cv2.imshow("Image with Bounding Boxes", i3)
    cv2.waitKey(1)

    return i3 / 255.0


actor_list = []
try:
    client = carla.Client('localhost', 2000)
    client.set_timeout(2.0)

    world = client.get_world()

    blueprint_library = world.get_blueprint_library()

    bp = blueprint_library.filter('model3')[0]
    print(bp)

    spawn_point = random.choice(world.get_map().get_spawn_points())

    vehicle = world.spawn_actor(bp, spawn_point)
    vehicle.apply_control(carla.VehicleControl(throttle=1.0, steer=0.0))

    actor_list.append(vehicle)

    # Get the blueprint for the RGB camera sensor
    blueprint = blueprint_library.find('sensor.camera.rgb')
    blueprint.set_attribute('image_size_x', f'{IM_WIDTH}')
    blueprint.set_attribute('image_size_y', f'{IM_HEIGHT}')
    blueprint.set_attribute('fov', '110')

    # Adjust sensor position relative to vehicle
    spawn_point = carla.Transform(carla.Location(x=2.5, z=0.7))

    # Spawn the camera sensor and attach it to the vehicle
    sensor = world.spawn_actor(blueprint, spawn_point, attach_to=vehicle)

    actor_list.append(sensor)

    # Listen to the sensor and process images
    sensor.listen(lambda data: process_img(data))

    time.sleep(5)

finally:
    print('destroying actors')
    for actor in actor_list:
        actor.destroy()
    print('done.')
