def generate_urls(file, image):
    image = image.replace(" ", "%20")  # Encode spaces as %20
    url = f"https://raw.githubusercontent.com/kal-elf2/MTRM-RPG/master/images/{file}/{image}.png"
    return url

def generate_gif_urls(file, image):
    image = image.replace(" ", "%20")  # Encode spaces as %20
    url = f"https://raw.githubusercontent.com/kal-elf2/MTRM-RPG/master/images/{file}/{image}.gif"
    return url
