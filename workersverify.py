import mysql.connector

# Укажите параметры подключения к вашей MySQL базе данных
config = {
    'user': 'yuriy',
    'password': 'Ak4B7V$S',
    'host': 'workersverify.cjlqzfuxt4xp.eu-north-1.rds.amazonaws.com',  # Например, 'localhost' или IP-адрес сервера MySQL
    'database': 'workersverify',
    'raise_on_warnings': True  # Если вы хотите, чтобы библиотека бросала исключения на предупреждения
}

# Создайте подключение к базе данных
try:
    cnx = mysql.connector.connect(**config)
    print("Успешно подключено к MySQL базе данных")
except mysql.connector.Error as err:
    print(f"Ошибка при подключении к MySQL: {err}")
    exit(1)

# Выполните SQL-запросы или другие операции с базой данных здесь

# Закройте соединение с базой данных
cnx.close()
