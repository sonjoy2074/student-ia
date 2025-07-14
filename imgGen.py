import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()
client = OpenAI()

st.set_page_config(page_title="🖼️ Student-ia Image Generator", layout="centered")
st.title("🧠🎨 Student-ia Image Creator")
st.markdown("Describe your scene and customize its look. We’ll create an AI-generated image for you!")

# ==== User Inputs ====
prompt = st.text_area("📝 Describe the image you want", placeholder="e.g., A medieval library filled with glowing runes")

col1, col2 = st.columns(2)
with col1:
    image_style = st.selectbox("🎨 Style", ["Photorealistic", "Cartoon", "Anime", "Digital Painting", "3D Render"])
    lighting = st.selectbox("💡 Lighting", ["Natural", "Warm", "Cool", "Cinematic", "Dramatic"])
with col2:
    medium = st.selectbox("🖌️ Medium", ["Pencil Sketch", "Watercolor", "Oil Painting", "Charcoal", "Digital Brush"])
    mood = st.selectbox("🌤️ Mood", ["Peaceful", "Epic", "Dark", "Happy", "Melancholic"])

resolution = st.selectbox("🖼️ Resolution", ["1024x1024", "1024x1792 (portrait)", "1792x1024 (landscape)"])

# ==== Button ====
if st.button("🚀 Generate Image") and prompt:
    with st.spinner("Creating your image..."):

        # Combine everything into a creative prompt
        full_prompt = f"""
Create an image in {image_style.lower()} style using a {medium.lower()} medium.
The lighting should be {lighting.lower()} and the overall mood should feel {mood.lower()}.
Scene: {prompt}
"""

        size_map = {
            "1024x1024": "1024x1024",
            "1024x1792 (portrait)": "1024x1792",
            "1792x1024 (landscape)": "1792x1024"
        }

        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=full_prompt.strip(),
                size=size_map[resolution],
                quality="standard",
                n=1
            )
            image_url = response.data[0].url
            st.image(image_url, caption="✅ Generated Image", use_column_width=True)
        except Exception as e:
            st.error(f"❌ Error generating image: {e}")
