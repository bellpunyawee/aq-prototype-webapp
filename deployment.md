# Deployment Guide

This guide will help you deploy your application to a production environment.

## Deploy on Self-hosted Server with Github Actions
![image](https://github.com/bellpunyawee/AQ_Prototype/assets/43726547/4997f878-a2fd-4523-83fe-a5d2178d0478)

Steps to deploy on your own server with Github Actions:

- Push your code to a Github repository on Branch `main`
- Wait for Github Actions to build and deploy your application to your server

## Migration Database

### Requirements
- SSH access to your server
- Database file if you want to export the database
- Stay in the root directory of your project

### Import Database
![image](https://github.com/bellpunyawee/AQ_Prototype/assets/43726547/f47a33a3-cd0d-4cc5-9cbd-75c28de1a85c)


for development, you can use the following command to import the database:
Run `scp -r <from remote> <to host>` to copy your database to your server

Example:

```bash
scp -r vm@154.215.14.236:/home/vm/db .
```

### Export Database

for force migration, you can use the following command to export the database:
Run `scp -r <from host> <to remote>` to copy your database to your server

Example:
```bash
ssh vm@154.215.14.236 'rm -rf /home/vm/db'
scp -r ./db vm@154.215.14.236:/home/vm
```
> Note: Don't push your database to your repository on Github!
