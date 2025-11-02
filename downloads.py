import os
from weasyprint import *


def create_card(
    avatar: str,
    username: str,
    name: str,
    surname: str,
    rating: float,
    grade: str,
    faculty: str,
    id: str,
):
    base_dir = os.path.dirname(os.path.abspath(__file__))

    html_markup = open("templates/user_card/user_card.html").read()

    html_markup = html_markup.replace("AVATAR_PATH", avatar)
    html_markup = html_markup.replace("USERNAME", username)
    html_markup = html_markup.replace("NAME_SURNAME", f"{name} {surname}")
    html_markup = html_markup.replace("RATING", f"{rating}")
    html_markup = html_markup.replace("GRADE_FACULTY", f"{grade} {faculty}")

    HTML(string=html_markup, base_url=base_dir).write_pdf(
        f"user_cards/{id}.pdf",
        stylesheets=[CSS(string="@page { size: A4; margin: 0; }")],
    )


def download_event(event_data, participants):
    """
    Создает PDF-карточку события для скачивания

    :param event_data: словарь с данными о событии
    :param participants: список участников события
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Читаем HTML шаблон
    html_markup = open(
        "templates/event_card/event_card.html", "r", encoding="utf-8"
    ).read()

    # Заменяем плейсхолдеры на реальные данные
    html_markup = html_markup.replace("EVENT_TITLE", event_data.get("title", "Событие"))
    html_markup = html_markup.replace(
        "EVENT_TYPE", event_data.get("type", "Мероприятие")
    )
    html_markup = html_markup.replace("EVENT_DATE", str(event_data.get("datetime", "")))
    html_markup = html_markup.replace(
        "EVENT_CONTENT", event_data.get("content", "Описание отсутствует")
    )

    # Обрабатываем изображение
    image_path = event_data.get("image", "")
    if image_path and os.path.exists(f"static/{image_path}"):
        html_markup = html_markup.replace("IMAGE_PATH", f"static/{image_path}")
    else:
        html_markup = html_markup.replace('src="IMAGE_PATH"', 'src=""')

    # Форматируем список участников
    participants_html = ""
    if participants and participants != [""]:
        for i, participant_id in enumerate(participants, 1):
            if participant_id:  # Проверяем, что participant_id не пустой
                try:
                    # Получаем информацию о пользователе по ID
                    user_data = safe_db_operation(
                        connection.get_user_by_id, "users", participant_id
                    )
                    if user_data != -1:
                        participant_name = f"{user_data['name']} {user_data['surname']} (@{user_data['username']})"
                        participants_html += f"<p>{i}. {participant_name}</p>"
                except Exception as e:
                    logger.log(
                        "error",
                        f"Error getting user data for participant {participant_id}: {e}",
                    )
                    participants_html += f"<p>{i}. Участник ID: {participant_id}</p>"
    else:
        participants_html = "<p>Участники пока не зарегистрированы</p>"

    html_markup = html_markup.replace("PARTICIPANTS_LIST", participants_html)

    # Создаем безопасное имя файла
    safe_title = "".join(
        c
        for c in event_data.get("title", "event")
        if c.isalnum() or c in (" ", "-", "_")
    ).rstrip()
    filename = f"{safe_title}.pdf"
    filepath = f"event_cards/{filename}"

    # Создаем директорию если не существует
    os.makedirs("event_cards", exist_ok=True)

    # Генерируем PDF
    try:
        HTML(string=html_markup, base_url=base_dir).write_pdf(
            filepath, stylesheets=[CSS(string="@page { size: A4; margin: 20mm; }")]
        )
        return filename
    except Exception as e:
        logger.log("error", f"Error generating event PDF: {e}")
        # Возвращаем имя файла даже при ошибке, чтобы не ломать интерфейс
        return filename


def create_event_card(event_data, participants):
    """
    Создает PDF-карточку события (альтернативное название для совместимости)

    :param event_data: словарь с данными о событии
    :param participants: список участников события
    """
    return download_event(event_data, participants)
