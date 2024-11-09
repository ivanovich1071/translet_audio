import openai
import speech_recognition as sr
import os
import csv
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.utils import which

# Указываем путь к ffmpeg в pydub
AudioSegment.converter = which("ffmpeg")

# Загрузка переменных окружения из .env
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Путь к папке с аудиофайлами
audio_folder = "audio"

# Список для записи результатов
results = [
    ["Имя файла", "Общий тон диалога", "Вопросы клиента", "Ответы менеджера", "Выявленные проблемы", "Рекомендации"]]


def transcribe_audio(file_path):
    recognizer = sr.Recognizer()

    # Конвертация аудио в WAV, если формат другой
    if not file_path.endswith(".wav"):
        audio = AudioSegment.from_file(file_path)
        file_path = file_path.replace(file_path.split('.')[-1], "wav")
        audio.export(file_path, format="wav")

    # Транскрибация аудио в текст
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
        try:
            transcript = recognizer.recognize_google(audio_data, language="ru-RU")  # Замените "ru-RU" на нужный язык
            return transcript
        except sr.UnknownValueError:
            return "Не удалось распознать речь."
        except sr.RequestError as e:
            return f"Ошибка запроса к сервису Google Speech Recognition: {e}"


def analyze_transcript(transcript):
    # Промт для анализа
    prompt = f"""
    Проанализируй текст диалога между клиентом и менеджером:
    1. Опиши общий тон общения.
    2. Перечисли ключевые вопросы клиента.
    3. Перечисли ответы менеджера.
    4. Выяви любые проблемы, которые были решены или остались нерешенными.
    5. Предложи краткие рекомендации для улучшения взаимодействия с клиентом.
    """

    # Получение ответа от модели OpenAI
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"{prompt}\n\nТекст диалога:\n{transcript}",
        temperature=0.5,
        max_tokens=1500
    )
    return response.choices[0].text.strip()


# Проход по каждому файлу в папке и обработка
for filename in os.listdir(audio_folder):
    if filename.endswith(".mp3") or filename.endswith(".wav"):
        # Путь к аудиофайлу
        file_path = os.path.join(audio_folder, filename)

        # Транскрибация аудио в текст
        transcript = transcribe_audio(file_path)

        # Если транскрипция прошла успешно, анализируем текст
        if transcript and "Ошибка" not in transcript:
            analysis = analyze_transcript(transcript)

            # Разделение анализа на компоненты
            analysis_lines = analysis.split('\n')
            tone = analysis_lines[0].replace("Общий тон диалога: ", "")
            questions = analysis_lines[1].replace("Вопросы клиента: ", "")
            answers = analysis_lines[2].replace("Ответы менеджера: ", "")
            issues = analysis_lines[3].replace("Выявленные проблемы: ", "")
            recommendations = analysis_lines[4].replace("Рекомендации: ", "")

            # Добавление результатов в список
            results.append([filename, tone, questions, answers, issues, recommendations])
        else:
            # Если транскрипция не удалась, добавляем сообщение об ошибке
            results.append([filename, "Ошибка транскрипции", "", "", "", ""])

# Запись результатов в CSV файл
csv_file = "dialogue_analysis.csv"
with open(csv_file, mode="w", newline='', encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerows(results)

print(f"Результаты транскрипции и анализа записаны в {csv_file}.")
