import streamlit as st
import sqlite3
import openai
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Database setup
DB_FILE = "recipes.db"
openai.api_key = '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'  # Replace with your actual OpenAI API key


def setup_database():
    """Ensures the database and recipes table exist without UNIQUE constraints."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredients TEXT,
            cuisine TEXT,
            gravy_level TEXT,
            recipe TEXT,
            image_url TEXT,
            youtube_link TEXT
        )
    ''')
    conn.commit()
    conn.close()

setup_database()

def get_existing_recipes(ingredients, cuisine, gravy_level):
    """Fetch all existing recipes for given ingredients, cuisine, and gravy level."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT recipe, image_url, youtube_link FROM recipes 
        WHERE ingredients = ? AND cuisine = ? AND gravy_level = ?
    """, (ingredients, cuisine, gravy_level))
    existing_recipes = cursor.fetchall()
    conn.close()
    return existing_recipes

def save_recipe(ingredients, cuisine, gravy_level, recipe, image_url, youtube_link):
    """Save a new recipe into the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO recipes (ingredients, cuisine, gravy_level, recipe, image_url, youtube_link) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (ingredients, cuisine, gravy_level, recipe, image_url, youtube_link))
    conn.commit()
    conn.close()
def display_image(image_url):
    """Check if an image URL is valid and display it."""
    if image_url and image_url.startswith("http"):
        try:
            st.image(image_url, width=500, caption="Recipe Image")
        except Exception as e:
            st.warning(f"⚠️ Unable to load image: {e}")
            st.image("default_food.jpg", width=500, caption="Default Recipe Image")
    else:
        st.image("default_food.jpg", width=500, caption="Default Recipe Image")

def generate_recipe(ingredients, cuisine, gravy_level):
    """Generate a recipe using OpenAI, including an image URL and a YouTube link."""
    prompt = f"Create a {gravy_level} {cuisine} style recipe using {ingredients}. Keep it simple."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    recipe = response['choices'][0]['message']['content'].strip()
    
    image_url = f"https://source.unsplash.com/600x400/?{cuisine},food"  # Placeholder for food images
    youtube_link = f"https://www.youtube.com/results?search_query={cuisine}+recipe"
    
    return recipe, image_url, youtube_link

def generate_pdf(recipe_text, filename):
    """Generate and return a PDF file path."""
    pdf_path = os.path.join("recipes", filename)
    os.makedirs("recipes", exist_ok=True)
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Recipe:")
    y = 730
    for line in recipe_text.split("\n"):
        c.drawString(100, y, line)
        y -= 20
    c.save()
    return pdf_path

# Streamlit UI
st.markdown("""
    <style>
    .title {text-align: center; font-size: 40px; font-weight: bold; color: #FF5733;}
    .subtitle {font-size: 20px; font-weight: bold; color: #2E86C1;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>🍽️ AI Recipe Maker</div>", unsafe_allow_html=True)

# User Input Section
ingredients = st.text_area("🛒 Enter ingredients (comma-separated):")
cuisine = st.selectbox("🌍 Select cuisine type:", ["Indian", "Italian", "Chinese", "Mexican", "American", "French", "Other"], index=0)
gravy_level = st.selectbox("🥣 Choose gravy level:", ["Light", "Medium", "Thick"], index=1)

if st.button("🔍 Generate Recipe"):
    if ingredients:
        ingredients_cleaned = ", ".join([i.strip() for i in ingredients.split(",")])
        existing_recipes = get_existing_recipes(ingredients_cleaned, cuisine, gravy_level)

        if existing_recipes:
            st.success("✅ Found an existing recipe!")
            for recipe, image_url, youtube_link in existing_recipes:
                display_image(image_url)
                st.markdown(f"**🍛 Recipe:** {recipe}")
                st.markdown(f"[📺 Watch on YouTube]({youtube_link})")
        else:
            st.info("✨ Generating a new recipe...")
            new_recipe, image_url, youtube_link = generate_recipe(ingredients_cleaned, cuisine, gravy_level)
            save_recipe(ingredients_cleaned, cuisine, gravy_level, new_recipe, image_url, youtube_link)
            
            display_image(image_url)
            st.markdown(f"**🍛 Recipe:** {new_recipe}")
            st.markdown(f"[📺 Watch on YouTube]({youtube_link})")

            pdf_file = generate_pdf(new_recipe, "new_recipe.pdf")
            st.download_button("📥 Download Recipe", open(pdf_file, "rb"), file_name="new_recipe.pdf")
    else:
        st.warning("⚠️ Please enter ingredients to generate a recipe!")
