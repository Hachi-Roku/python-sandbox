from fastapi import APIRouter, Form, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

import random

import os
from fastapi import APIRouter, Form, HTTPException
from dotenv import load_dotenv
import httpx

# Loading data from .env
load_dotenv()

# Retreiving secret key from env
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

# Create the router
process_image_router = APIRouter()

# Initialize Jinja2Templates
templates = Jinja2Templates(directory="src/templates")

@process_image_router.post("/processed-image", response_class=HTMLResponse)
async def processed_image(request: Request, file: UploadFile, shift: int = Form(...), captcha_response: str = Form(...)):
    # Verify reCAPTCHA if needed
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": RECAPTCHA_SECRET_KEY,
                "response": captcha_response
            }
        )
        result = response.json()

    if not result.get("success"):
        raise HTTPException(status_code=400, detail="Ошибка верификации reCAPTCHA")

    # Open the image
    image = Image.open(file.file)
    image_np = np.array(image)

    # Apply the selected version of the shift
    processed_image = apply_shift(image_np, shift)

    # Save the processed image to a BytesIO buffer
    buffered = io.BytesIO()
    Image.fromarray(processed_image).save(buffered, format="PNG")
    buffered.seek(0)

    # Encode the processed image as base64
    processed_image_base64 = base64.b64encode(buffered.getvalue()).decode()

    # Encode the graph as base64
    graph_base64 = generate_color_distribution_graph_base64(image_np)

    # Render the template with the base64-encoded images
    return templates.TemplateResponse(
        "upload-result.html",
        {
            "request": request,
            "image_data": processed_image_base64,
            "graph_data": graph_base64,
        }
    )

def apply_shift(image_np, shift):
    h, w, channels = image_np.shape

    # Iterate over layers, starting from the outermost rectangle and working inward
    for layer in range(0, min(h, w) // 2, shift):
        # Define the boundaries of the current layer with the thickness equal to shift
        top = layer
        bottom = h - layer - 1
        left = layer
        right = w - layer - 1

        if top + shift >= bottom or left + shift >= right:
            break

        # Extract the top, right, bottom, and left edges of the layer with thickness equal to shift
        top_edge = image_np[top:top + shift, left:right + 1].copy()
        right_edge = image_np[top + shift:bottom + 1 - shift, right:right + shift].copy()
        bottom_edge = image_np[bottom - shift + 1:bottom + 1, left:right + 1][::-1].copy()
        left_edge = image_np[top + shift:bottom + 1 - shift, left:left + shift][::-1].copy()

        # Check if any of the edges have a size of zero and skip if necessary
        if top_edge.size == 0 or right_edge.size == 0 or bottom_edge.size == 0 or left_edge.size == 0:
            continue

        # Concatenate the edges to form a single array representing the perimeter for all channels
        perimeter = np.concatenate([top_edge.reshape(-1, channels),
                                    right_edge.reshape(-1, channels),
                                    bottom_edge.reshape(-1, channels),
                                    left_edge.reshape(-1, channels)], axis=0)

        # Choose a random direction for shifting
        direction = random.choice(["up", "down", "left", "right"])

        # Perform cyclic shift on the perimeter using the specified shift amount
        if direction in ["up", "left"]:
            perimeter = np.roll(perimeter, -shift, axis=0)
        else:  # "down" or "right"
            perimeter = np.roll(perimeter, shift, axis=0)

        # Split the shifted perimeter back into the four edges
        top_edge_new = perimeter[:top_edge.size // channels].reshape(top_edge.shape)
        right_edge_new = perimeter[
            top_edge.size // channels:top_edge.size // channels +
            right_edge.size // channels
        ].reshape(right_edge.shape)
        bottom_edge_new = perimeter[
            top_edge.size // channels +
            right_edge.size // channels:top_edge.size // channels +
            right_edge.size // channels +
            bottom_edge.size // channels
        ][::-1].reshape(bottom_edge.shape)
        left_edge_new = perimeter[-(left_edge.size // channels):][::-1].reshape(left_edge.shape)

        # Reassign the shifted values back to the image
        image_np[top:top + shift, left:right + 1] = top_edge_new
        image_np[top + shift:bottom + 1 - shift, right:right + shift] = right_edge_new
        image_np[bottom - shift + 1:bottom + 1, left:right + 1] = bottom_edge_new
        image_np[top + shift:bottom + 1 - shift, left:left + shift] = left_edge_new

    return image_np

def generate_color_distribution_graph_base64(image_np):
    # Create a figure for the color distribution graph
    plt.figure()
    colors = ['red', 'green', 'blue']
    channel_names = ['Red', 'Green', 'Blue']

    # Plot histograms for each color channel
    for channel, color in enumerate(colors):
        plt.hist(
            image_np[:, :, channel].ravel(),
            bins=256,
            color=color,
            alpha=0.6,
            label=f'{channel_names[channel]} Channel'
        )

    # Add labels and title
    plt.legend()
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.title("Color Distribution")

    # Save the graph to a BytesIO buffer
    graph_buffer = io.BytesIO()
    plt.savefig(graph_buffer, format="PNG")
    graph_buffer.seek(0)

    # Encode the graph as base64
    graph_base64 = base64.b64encode(graph_buffer.getvalue()).decode()

    return graph_base64
