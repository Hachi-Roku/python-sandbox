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
async def processed_image(request: Request, file: UploadFile, shift: int = Form(...), is_v2: bool = Form(False), captcha_response: str = Form(...)):
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
    if is_v2:
        processed_image = apply_shift_v2(image_np, shift)
    else:
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
    h, w, _ = image_np.shape

    # Iterate over layers, starting from the outermost rectangle and working inward
    for layer in range(0, min(h, w) // 2, shift):
        # Define the boundaries of the current layer
        top = layer
        bottom = h - layer - 1
        left = layer
        right = w - layer - 1

        if top >= bottom or left >= right:
            break

        # Extract the top, right, bottom, and left edges of the layer
        top_edge = image_np[top, left:right + 1].copy()
        right_edge = image_np[top + 1:bottom + 1, right].copy()
        bottom_edge = image_np[bottom, left:right + 1][::-1].copy()
        left_edge = image_np[top + 1:bottom + 1, left][::-1].copy()

        # Concatenate the edges to form a single array representing the perimeter
        perimeter = np.concatenate([top_edge, right_edge, bottom_edge, left_edge])

        # Choose a random direction for shifting
        direction = random.choice(["up", "down", "left", "right"])

        # Perform cyclic shift on the perimeter using the specified shift amount
        if direction in ["up", "left"]:
            perimeter = np.roll(perimeter, -shift, axis=0)
        else:  # "down" or "right"
            perimeter = np.roll(perimeter, shift, axis=0)

        # Calculate the lengths of each edge
        top_length = right - left + 1
        right_length = bottom - top
        bottom_length = right - left + 1
        left_length = bottom - top

        # Split the shifted perimeter back into the four edges
        top_edge_new = perimeter[:top_length]
        right_edge_new = perimeter[top_length:top_length + right_length]
        bottom_edge_new = perimeter[top_length + right_length:top_length + right_length + bottom_length][::-1]
        left_edge_new = perimeter[-left_length:][::-1]

        # Reassign the shifted values back to the image
        image_np[top, left:right + 1] = top_edge_new
        image_np[top + 1:bottom + 1, right] = right_edge_new
        image_np[bottom, left:right + 1] = bottom_edge_new
        image_np[top + 1:bottom + 1, left] = left_edge_new

    return image_np

def apply_shift_v2(image_np, shift):
    h, w, _ = image_np.shape

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

        # Concatenate the edges to form a single array representing the perimeter
        perimeter = np.concatenate([top_edge.flatten(), right_edge.flatten(), bottom_edge.flatten(), left_edge.flatten()])

        # Choose a random direction for shifting
        direction = random.choice(["up", "down", "left", "right"])

        # Perform cyclic shift on the perimeter using the specified shift amount
        if direction in ["up", "left"]:
            perimeter = np.roll(perimeter, -shift, axis=0)
        else:  # "down" or "right"
            perimeter = np.roll(perimeter, shift, axis=0)

        # Split the shifted perimeter back into the four edges
        top_edge_size = top_edge.size
        right_edge_size = right_edge.size
        bottom_edge_size = bottom_edge.size
        left_edge_size = left_edge.size

        # Ensure reshaping only occurs when the sizes match
        top_edge_new = perimeter[:top_edge_size].reshape(top_edge.shape)
        right_edge_new = perimeter[top_edge_size:top_edge_size + right_edge_size].reshape(right_edge.shape)
        bottom_edge_new = perimeter[top_edge_size + right_edge_size:top_edge_size + right_edge_size + bottom_edge_size][::-1].reshape(bottom_edge.shape)
        left_edge_new = perimeter[-left_edge_size:][::-1].reshape(left_edge.shape)

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
