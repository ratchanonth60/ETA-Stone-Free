# ETA


## Getting Started

This project is a sophisticated e-commerce platform built on the powerful Django framework. It is designed to deliver a seamless and scalable online shopping experience, catering to businesses of all sizes. The platform integrates a wide array of functionalities essential for modern e-commerce websites.

## Key Features

- Robust Product Management: Utilizing Django Oscar, the platform offers extensive features for product listing, categorization, and inventory management.

- Search Engine Optimization: Integrated with Whoosh and -Django Haystack, the platform provides advanced search capabilities, ensuring products are easily discoverable.

- Secure Payment Processing: Incorporates Stripe for reliable and secure payment transactions.

- High-Performance ORM: Uses psycopg2 for efficient database management, crucial for handling large volumes of e-commerce data.

- User-Friendly Interface: Leverages Django's powerful templating to offer a user-friendly and responsive interface.

- Scalability and Performance: Powered by Celery for asynchronous task management and Redis for caching, ensuring high performance and scalability.

- Customizability and Extensibility: The platform is highly customizable with Django's modular architecture, allowing for easy integration of additional features like social authentication, thumbnail generation (sorl-thumbnail), and more.

- Developer Tools: Equipped with a suite of developer tools including Django Debug Toolbar and various testing libraries like pytest and factory_boy, ensuring a robust development process.

- Security and Compliance: Incorporates industry-standard security practices and is compliant with modern web standards.

### Installing

A step by step series of examples that tell you how to get a development
environment running

Say what the step will be

    Give the example

And repeat

    until finished

End with an example of getting some data out of the system or using it
for a little demo

---

# Makefile

This README provides an overview and instructions for using the Docker Compose workflow implemented in this project. It explains the purpose of various scripts and commands in the `Makefile` and how to use them effectively.

### Key Files

- **COMPOSE_FILE_DEV**: `docker/dev/docker-compose.yml` - Used for development environment setup.
- **COMPOSE_FILE_DEPLOY**: `docker/deploy/docker-compose.yml` - Used for production deployment.

## Makefile Tasks

### Helper Functions

- `set-compose-file`: Selects the appropriate Docker Compose file based on the environment.

### Basic Commands

- **help**: Displays help information for each task.
- **backup**: Backs up tenant databases.
- **restore**: Restores database from a backup file.
- **build**: Builds the release and development container.
- **ssh**: Runs container in development mode.
- **start**: Starts services based on the environment.
- **up**: Spins up the containers.
- **update**: Updates the containers.
- **stop**: Stops services based on the environment.
- **restart**: Restarts services based on the environment.
- **rm**: Stops and removes running containers.
- **ps**: Processes running containers.
- **logs**: Shows logs for running containers.
- **clean**: Cleans the generated/compiled files.
- **list**: Lists Docker processes, images, and networks.
- **deploy**: Deploys the application.

### Advanced Commands

- **migrate**: Executes Django database migrations.
- **makemigrations**: Creates new migrations based on models changes.
- **tests**: Runs tests in the container.
- **lint**: Runs linter in the container.
- **static**: Collects static files for the web service.

## Usage

### Setting Up

Before running any task, ensure Docker is installed and configured on your system.

### Executing Commands

To execute a command, use `make [command]`. For example:

- To build containers, run `make build`.
- To start the application, run `make up`.
- To back up the database, run `make backup`.

### Customizing Commands

You can customize commands by setting environment variables. For instance:

- Set `env=prod` for production or `env=dev` for development.
- Use `target` to specify specific services.

## Backup and Restore

- **Backup**: Backups are stored in the `backups` directory.
- **Restore**: Use the `restore` command with the appropriate SQL file for database restoration.

## Deployment

Run `make deploy` to build and start the application. This will spin up necessary containers, including `nginx-proxy`, `web-deploy`, and `acme-companion`.

## Further Assistance

For additional help or troubleshooting, refer to the Docker and Docker Compose documentation or contact the development team.

---
chown -R 1000
One Paragraph of the project description

Initially appeared on
[gist](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2). But the page cannot open anymore so that is why I have moved it here.