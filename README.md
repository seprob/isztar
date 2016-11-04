# Isztar

## Synopsis

Isztar is a tool used for removing tags from the Docker Registry repository.

After removing tags you should run the following command on your Registry server to delete images from the disk with Garbage Collect (with root privileges):
```
docker exec -it dockerregistry_registry_v2_1 bin/registry garbage-collect /etc/docker/registry/config.yml
```
Change "dockerregistry_registry_v2_1" to your Registry container name.

## Usage

You should use Python 2 to run this application.

Before you run Isztar, modify the "constants.json" file according to your requirements:
- "hostname": host name of your Docker Registry server,
- "user": name of the user to login,
- "password": user password to login,
- "no_images_to_left": how many images in each repository Isztar should leave (Isztar sorts images by create date from the oldest to the newest).

If you are ready to run, type
```
python isztar.py
```