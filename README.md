# Boxed
A script that creates and runs docker containers for ctf challenge.

Two containers are created, one for the player and one for the challenge. 
The idea is to quickly create an simple environment for the player to run the challenge.

Once two containers are created, ssh into the player container to solve the challenge.


## Installation
```
$ git clone https://github.com/Howard-12/boxed.git
$ cd boxed
$ chmod +x install.sh
$ ./install.sh
```

## Usage
Run the script in the directory where the challenge is located.
```
boxed <challenge file>
```

This will create all necessary files and also start the containers.

**NOTE**: run the script again in different directory will stop and remove all current running challenge containers,
and start a new one in the new directory.

**Stop the containers**
```
boxed <challenge file> --down
# or
docker-compose down
```

**Clean up containers**
```
boxed <challenge file> --clean
```

## Future
[] Create containers based on the challenge type (e.g. web)

