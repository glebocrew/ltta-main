
def create_card(avatar: str, username: str, name: str, surname: str, rating: float, grade: str, faculty: str, id: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))

    html_markup = open("templates/user_card/user_card.html").read()

    html_markup = html_markup.replace("AVATAR_PATH", avatar)
    html_markup = html_markup.replace("USERNAME", username)
    html_markup = html_markup.replace("NAME_SURNAME", f"{name} {surname}")
    html_markup = html_markup.replace("RATING", f"{rating}")
    html_markup = html_markup.replace("GRADE_FACULTY", f"{grade} {faculty}")

    HTML(string=html_markup, base_url=base_dir).write_pdf(f'user_cards/{id}.pdf')

