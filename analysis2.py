import openai
import os
import csv
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Путь к папке с текстовыми файлами
text_folder = "."

# Список для записи результатов
results = [
    ["Имя файла", "Общий тон диалога", "Вопросы клиента", "Ответы менеджера", "Выявленные проблемы", "Рекомендации"]
]

def translate_text(text, target_language="ru"):
    """Перевод текста на указанный язык с использованием модели OpenAI."""
    translation_prompt = f"Переведи следующий текст на русский язык:\n\n{text}"
    response = openai.ChatCompletion.create(
        model="gpt-4",  # или используйте "gpt-3.5-turbo" в зависимости от вашей подписки
        messages=[
            {"role": "system", "content": "Ты переводчик с английского на русский."},
            {"role": "user", "content": translation_prompt}
        ],
        temperature=0.5,
    )
    return response['choices'][0]['message']['content'].strip()

def analyze_transcript(transcript):
    """Анализ текста диалога с помощью модели OpenAI."""
    prompt = f"""
    Проанализируй текст диалога между клиентом и менеджером:
    1. Опиши общий тон общения.
    2. Перечисли ключевые вопросы клиента.
    3. Перечисли ответы менеджера.
    4. Выяви любые проблемы, которые были решены или остались нерешенными.
    5. Предложи краткие рекомендации для улучшения взаимодействия с клиентом.
    """

    # Выполнение анализа с OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ты помощник для анализа диалогов."},
            {"role": "user", "content": f"{prompt}\n\nТекст диалога:\n{transcript}"}
        ],
        temperature=0.5,
    )
    return response['choices'][0]['message']['content'].strip()

# Чтение и обработка каждого файла в папке
for filename in os.listdir(text_folder):
    if filename.endswith(".txt"):
        # Путь к текстовому файлу
        file_path = os.path.join(text_folder, filename)

        # Чтение текста из файла
        with open(file_path, "r", encoding="utf-8") as file:
            original_text = file.read()

        # Перевод текста на русский
        translated_text = translate_text(original_text)

        # Анализ переведенного текста
        analysis = analyze_transcript(translated_text)

        # Разделение анализа на компоненты
        analysis_lines = analysis.split('\n')
        tone = analysis_lines[0].replace("Общий тон диалога: ", "")
        questions = analysis_lines[1].replace("Вопросы клиента: ", "")
        answers = analysis_lines[2].replace("Ответы менеджера: ", "")
        issues = analysis_lines[3].replace("Выявленные проблемы: ", "")
        recommendations = analysis_lines[4].replace("Рекомендации: ", "")

        # Добавление результатов в список
        results.append([filename, tone, questions, answers, issues, recommendations])

# Запись результатов в CSV файл
csv_file = "dialogue_analysis.csv"
with open(csv_file, mode="w", newline='', encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerows(results)

print(f"Результаты анализа текстов записаны в {csv_file}.")
