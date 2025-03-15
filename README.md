
Enjoy playing around: https://pht5sypm5h.us-east-1.awsapprunner.com/

# Game Oracle

**Game Oracle** is a containerized Flask web application that leverages OpenAI’s GPT-3.5-turbo and the RAWG API to recommend video games based on user descriptions or titles. With a retro gaming-inspired UI, the app displays personalized game recommendations complete with metadata (cover images, release dates, ratings, and links) in an engaging, responsive interface.

Below is a sample GitHub README that describes your project in detail. You can adjust it as needed:

---

```markdown
# Game Oracle

**Game Oracle** is a containerized Flask web application that leverages OpenAI’s GPT-3.5-turbo and the RAWG API to recommend video games based on user descriptions or titles. With a retro gaming-inspired UI, the app displays personalized game recommendations complete with metadata (cover images, release dates, ratings, and links) in an engaging, responsive interface.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Docker Usage](#docker-usage)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Personalized Recommendations:**  
  Generate 5 game recommendations based on a natural language description. If a game title is provided, it suggests that game and related titles.
- **API Integrations:**  
  Utilizes OpenAI’s GPT-3.5-turbo for natural language processing and the RAWG API for game metadata.
- **Modern UX:**  
  Responsive UI with retro gaming aesthetics, dynamic ticker animations, and social links.
- **Robust Error Handling:**  
  Implements the Post/Redirect/Get pattern to avoid duplicate submissions and provides friendly error messages when issues occur.
- **Containerized & Cloud-Ready:**  
  Packaged with Docker for consistent deployments, and integrated with AWS App Runner for scalable, 24/7 hosting.

## Tech Stack

- **Backend:** Python, Flask, Gunicorn  
- **APIs:** OpenAI GPT-3.5-turbo, RAWG API  
- **Containerization:** Docker  
- **Serverless Adapter:** Mangum (for AWS Lambda compatibility, if needed)  
- **Deployment:** AWS App Runner (with options for AWS Lambda/ECS)

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- An AWS account (for deployment)
- API keys from [OpenAI](https://beta.openai.com/) and [RAWG](https://rawg.io/apidocs)

### Local Development

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/game-oracle.git
   cd game-oracle
   ```

2. **Run Locally with Flask (for development):**

   ```bash
   python app.py
   ```
   
   The app will be available at [http://localhost:5000](http://localhost:5000).

3. **Run with Docker:**

   Build the Docker image:
   ```bash
   docker build -t video-games-describer .
   ```

   Run the Docker container (assuming Gunicorn is configured to listen on port 8080):
   ```bash
   docker run -p 8080:8080 video-games-describer
   ```
   
   Then access [http://localhost:8080](http://localhost:8080).

## Dockerfile

Your Dockerfile is set up to use the official Python 3.12-slim image, install dependencies, copy your application code, and start Gunicorn on port 8080:

```dockerfile
# Use the official Python 3.12-slim image
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 8080
EXPOSE 8080

# Run the app with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
```

## Deployment

### AWS App Runner

1. **Push to ECR:**  
   Tag and push your Docker image to an ECR repository in a supported region (e.g., US East (N. Virginia)):

   ```bash
   docker tag video-games-describer:latest 096771828335.dkr.ecr.us-east-1.amazonaws.com/video-games-describer:latest
   docker push 096771828335.dkr.ecr.us-east-1.amazonaws.com/video-games-describer:latest
   ```

2. **Create an App Runner Service:**  
   - Log in to the AWS App Runner console.
   - Create a new service using “Container registry” as the source.
   - Select your ECR repository and image tag.
   - Configure service settings (instance configuration, environment variables, etc.).
   - Deploy your service and obtain the public HTTPS URL.

3. **Custom Domain (Optional):**  
   Map your App Runner URL to a custom domain for a professional appearance.

### AWS Lambda Deployment (Optional)

If you prefer a serverless approach using AWS Lambda, you can update your Dockerfile to use the AWS Lambda base image and integrate with Mangum. (See project documentation for details.)

## Project Structure

```
game-oracle/
├── app.py                # Main Flask application
├── Dockerfile            # Docker build instructions
├── requirements.txt      # Python dependencies
├── templates/            # HTML templates (e.g., index.html)
└── static/               # Static assets (images, CSS, etc.)
```

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request with your changes. Follow best practices for code quality and testing.

## License

This project is licensed under the [MIT License](LICENSE).

---

This README gives a clear overview of your project, details the technology and deployment workflow, and includes instructions for local development and deployment. This project demonstrates proficiency in containerization, cloud deployment, and API integration—making it a strong portfolio piece for senior ML/AI/SWE roles when complemented with additional projects showcasing advanced ML systems.

Feel free to customize further as needed!
```

---

This README should be concise, clear, and detailed enough for both developers and hiring managers to understand your project's capabilities and technical stack. Let me know if you need any more modifications!
