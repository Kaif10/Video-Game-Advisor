
Enjoy playing around: https://pht5sypm5h.us-east-1.awsapprunner.com/

# Video-Game-Advisor

**Video-Game-Advisor** is a containerizedweb application that leverages OpenAI’s GPT-3.5-turbo and the RAWG API to recommend video games based on user descriptions. With a retro gaming-inspired UI, the app displays personalized game recommendations complete with metadata (cover images, release dates, ratings, and links) in an engaging, responsive interface.



---

```markdown
# Video-Game-Advisor

**Video-Game-Advisor** is a containerized Flask web application that leverages OpenAI’s GPT-3.5-turbo and the RAWG API to recommend video games based on user descriptions or titles. With a retro gaming-inspired UI, the app displays personalized game recommendations complete with metadata (cover images, release dates, ratings, and links) in an engaging, responsive interface.


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



## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request with your changes. Follow best practices for code quality and testing.


