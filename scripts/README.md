# MedConnect Scripts

This directory contains utility scripts for the MedConnect platform.

## Available Scripts

### `deploy.sh`

Deploys the MedConnect infrastructure to AWS.

```bash
./deploy.sh [environment] [region]
```

**Parameters:**
- `environment` (optional): The deployment environment (default: dev)
- `region` (optional): The AWS region to deploy to (default: us-east-1)

**Example:**
```bash
./deploy.sh prod us-west-2
```

### `seed_data.py`

Seeds the MedConnect database with sample data for testing and development.

```bash
python seed_data.py [--count COUNT] [--environment ENV]
```

**Parameters:**
- `--count` (optional): Number of sample records to create (default: 10)
- `--environment` (optional): The deployment environment (default: dev)

**Example:**
```bash
python seed_data.py --count 100 --environment dev
```

### `generate_docs.py`

Generates API documentation from the codebase.

```bash
python generate_docs.py [--output OUTPUT]
```

**Parameters:**
- `--output` (optional): Output directory for documentation (default: ./docs)

**Example:**
```bash
python generate_docs.py --output ./api-docs
```

## Adding New Scripts

When adding new scripts to this directory, please follow these guidelines:

1. Use a descriptive name that indicates the script's purpose
2. Include a shebang line at the top of the script
3. Add proper error handling and logging
4. Document the script in this README
5. Make the script executable with `chmod +x script_name.sh` for shell scripts 