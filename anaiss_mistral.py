import os
import csv
import json
from dotenv import load_dotenv
from mistralai import Mistral

# Загрузка переменных окружения из .env
load_dotenv()
mistral_api_key = os.getenv("MISTRAL_API_KEY")

# Папка для текстовых и JSON файлов
text_folder = "."
json_folder = "analysis_results"
os.makedirs(json_folder, exist_ok=True)

# Список для записи результатов
results = [
    ["Имя файла", "Общий тон диалога", "Вопросы клиента", "Ответы менеджера", "Выявленные проблемы", "Рекомендации"]
]


class MistralChat:
    def __init__(self):
        self.client = Mistral(api_key=mistral_api_key)
        self.model = "mistral-large-latest"

    def translate_text(self, text: str) -> str:
        translation_prompt = f"Переведи следующий текст на русский язык:\n\n{text}"
        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": translation_prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Ошибка перевода: {e}")
            return ""

    def analyze_transcript(self, transcript: str) -> dict:
        prompt = """
        Проанализируй текст диалога между клиентом и менеджером:
        1. Опиши общий тон общения.
        2. Перечисли ключевые вопросы клиента.
        3. Перечисли ответы менеджера.
        4. Выяви любые проблемы, которые были решены или остались нерешенными.
        5. Предложи краткие рекомендации для улучшения взаимодействия с клиентом.
        """
        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": f"{prompt}\n\nТекст диалога:\n{transcript}"}]
            )
            full_analysis = response.choices[0].message.content.strip()
            print(f"Анализ текста: {full_analysis[:100]}...")

            # Создание словаря с заполнением по разделам
            analysis_dict = {
                "tone": self.extract_section(full_analysis, "Общий тон общения", "Вопросы клиента"),
                "questions": self.extract_section(full_analysis, "Вопросы клиента", "Ответы менеджера"),
                "answers": self.extract_section(full_analysis, "Ответы менеджера", "Выявленные проблемы"),
                "issues": self.extract_section(full_analysis, "Выявленные проблемы", "Рекомендации"),
                "recommendations": self.extract_section(full_analysis, "Рекомендации")
            }

            print(f"Результаты анализа: {analysis_dict}")
            return analysis_dict
        except Exception as e:
            print(f"Ошибка анализа: {e}")
            return {
                "tone": "",
                "questions": "",
                "answers": "",
                "issues": "",
                "recommendations": ""
            }

    def extract_section(self, text, start_marker, end_marker=None):
        """Извлекает текст между start_marker и end_marker в заданном тексте."""
        try:
            start_index = text.index(start_marker) + len(start_marker)
            if end_marker:
                end_index = text.index(end_marker, start_index)
                return text[start_index:end_index].strip()
            else:
                return text[start_index:].strip()
        except ValueError:
            return ""


# Чтение и обработка каждого файла в папке
mistral_chat = MistralChat()

for filename in os.listdir(text_folder):
    if filename.endswith(".txt"):
        # Путь к текстовому файлу
        file_path = os.path.join(text_folder, filename)

        # Чтение текста из файла
        with open(file_path, "r", encoding="utf-8") as file:
            original_text = file.read()

        # Перевод текста на русский
        translated_text = mistral_chat.translate_text(original_text)

        # Анализ переведенного текста и сохранение в JSON
        analysis_dict = mistral_chat.analyze_transcript(translated_text)
        json_filename = os.path.join(json_folder, f"{os.path.splitext(filename)[0]}.json")
        with open(json_filename, "w", encoding="utf-8") as json_file:
            json.dump(analysis_dict, json_file, ensure_ascii=False, indent=4)

# Формирование CSV с результатами
for filename in os.listdir(json_folder):
    if filename.endswith(".json"):
        # Путь к JSON-файлу
        json_path = os.path.join(json_folder, filename)

        # Чтение данных из JSON
        with open(json_path, "r", encoding="utf-8") as json_file:
            analysis_dict = json.load(json_file)

        # Извлечение данных для записи в CSV
        results.append([
            filename.replace(".json", ".txt"),
            analysis_dict.get("tone", ""),
            analysis_dict.get("questions", ""),
            analysis_dict.get("answers", ""),
            analysis_dict.get("issues", ""),
            analysis_dict.get("recommendations", "")
        ])

# Запись результатов в CSV файл
csv_file = "dialogue_analysis.csv"
with open(csv_file, mode="w", newline='', encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerows(results)

print(f"Результаты анализа текстов записаны в {csv_file}.")
