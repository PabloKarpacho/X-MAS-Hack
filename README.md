# X-MAS-Hack
Хакатон по распознаванию вида документа

![2409ea111b496859403e25f22415afe60d5b02df](https://user-images.githubusercontent.com/95717191/215322880-38a3cff9-fbbc-4cbe-a162-fda7ff879748.png)


# Проблема
Проблема: большой бизнес — это всегда много договоров. При этом высококвалифицированные специалисты нередко задействованы в рутинных задачах по регистрации и анализу документов. Один из первых этапов работы с документами — маршрутизация. В зависимости от вида договора и других параметров выбирается дальнейший маршрут согласования и регламент проверки. Сроки от регистрации документа до того, как он попадает к нужному сотруднику могут достигать 14 дней.

Технологии: Python, Transformers, BERT, NLP, NLU, text classification, explainable ML decisions.

Данные для обучения: 120 договоров с указанием их видов.

# Задача
Задача: разработать решение для автоматического определения вида договора. Решение должно принимать на вход документ в форматах doc, docx, pdf и выдавать вид договора, а также интерпретировать результаты. Интерпретация результатов предполагает наличие признаков и критериев, по которым был выбран вид договора. Успех решение будет определяться не только по тому, насколько правильно определяется вид договора, но и по качеству интерпретации результатов.

Разработанное решение может быть использовано не только для автоматизации процесса по маршрутизации документов внутри компаний, но для выявления правовых рисков переквалификации договора и минимизации негативных последствий.

# Решение: 

Финальным решением задачм хакатона является телеграмм-бот: "DocumentTypeChecker"

![image](https://user-images.githubusercontent.com/95717191/215323182-a6d030d5-9755-4c1f-b48b-f7ff75cefe2e.png)



# Инструкции:
classes.json - инициальный документ с метками классов

dataset_noise.csv - сформированный размеченный и расширенный датасет с шумом

Document_type_checker.ipynb - тетрадка с ботом

Document_type_checker.py - файл с реализацией препроцессинга и бота

EDA_final.ipynb - тетрадка с эксплораторным анализом

keyphrases2.txt - текстовый файл с ключевыми фразами

LabelEncoder.pkl, logistic_model.pkl, tfidf.pkl - кодировщик, используемая модель и векторизатор

noise_class.json - документ с метками классов расширенного датасет

Textract запускать через докер образ:

docker run -p 8080:8080 bespaloff/textract-rest-api
