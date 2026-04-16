<template>
    <body>
    <div class="main-content">
        <h1 class="page-title">Наша команда</h1>
        
        <div class="team-container">
            <div class="team-member">
                <div class="member-header">

                    <div class="member-info">
                        <h3>Кабанов Илья Александрович</h3>
                        <div class="member-role">Team Lead</div>
                    </div>
                </div>
                <div class="member-responsibilities">
                    <ul class="responsibilities-list">
                      <li>Координация работы команды</li>
                      <li>Организация рабочих процессов и достижения целей проекта</li>
                      <li>Контроль сроков и выполнений задач</li>
                      <li>Взаимодействие с заказчиком</li>
                    </ul>
                </div>
            </div>
            <div class="team-member">
                <div class="member-header">
                    <div class="member-info">
                        <h3>Кушхов Руслан Алимович</h3>
                        <div class="member-role">Frontend Developer</div>
                    </div>
                </div>
                <div class="member-responsibilities">
                    <ul class="responsibilities-list">
                        <li>Разработка пользовательского интерфейса</li>
                        <li>Верстка адаптивных страниц</li>
                        <li>Оптимизация производительности</li>
                        <li>Финансист</li>
                    </ul>
                </div>
            </div>
            <div class="team-member">
                <div class="member-header">
                    <div class="member-info">
                        <h3>Каскинбаев Ильнур Фанисович</h3>
                        <div class="member-role">Backend-API Developer</div>
                    </div>
                </div>
                <div class="member-responsibilities">
                    <ul class="responsibilities-list">
                      <li>Разработка бэкенд-API и подключение модели к фронтенду</li>
                      <li>Сборка и тестирование интегрированного решения</li>
                      <li>Оптимизация производительности</li>
                      <li>Контейнеризация</li>
                    </ul>
                </div>
            </div>
            <div class="team-member">
                <div class="member-header">
                    <div class="member-info">
                        <h3>Чернов Никита Сергеевич</h3>
                        <div class="member-role">Machine learning</div>
                    </div>
                </div>
                <div class="member-responsibilities">
                    <ul class="responsibilities-list">
                      <li>Разработка парсера документов</li>
                      <li>Адаптация LLM для работы с БД Milvus</li>
                      <li>Обучение модели</li>
                    </ul>
                </div>
            </div>
            <div class="team-member">
                <div class="member-header">
                    <div class="member-info">
                        <h3>Ибрагимов Денис Димович</h3>
                        <div class="member-role">Machine learning</div>
                    </div>
                </div>
                <div class="member-responsibilities">
                    <ul class="responsibilities-list">
                      <li>Разработка пайплайна обработки запросов и получения ответа</li>
                      <li>Настройка эмбеддингов</li>
                      <li>Обучение модели</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="project-info">
            <h2 class="project-title">О проекте</h2>
            <p class="project-description">
                Наш логотип отражает суть команды A10 — объединение технологий и интеллекта. 
                Белая надпись a10 на насыщенном синем фоне символизирует чистоту идей, стабильность и инновации.
                Дизайн выполнен в современном минималистичном стиле, что делает логотип узнаваемым и ассоциирующимся с высокими технологиями. 
                Он идеально передаёт миссию нашей команды — создание AI-ассистента для интеллектуального распознавания текста, который делает взаимодействие с информацией проще и умнее.
            </p>
        </div>
    </div>
</body>
</template>
<style scoped>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Arial', sans-serif;
}

body {
    background: linear-gradient(135deg, #e6f2ff 0%, #ffffff 100%);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.top-bar {
    background: linear-gradient(135deg, #2c5aa0 0%, #1e3d6f 100%);
    color: white;
    padding: 15px 0;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.top-bar-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 24px;
    font-weight: bold;
    color: white;
}

.image_logo {
    height: 60px;
    width: auto;
    border-radius: 5px;
}

.nav-links {
    display: flex;
    gap: 20px;
}

.nav-links a {
    color: white;
    text-decoration: none;
    font-weight: 500;
    transition: all 0.5s;
}

.nav-links a:hover {
    opacity: 0.8;
    transform: scale(120%) translateY(-3.5px);
}

.main-content {
    flex: 1;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
    padding: 30px 10px;
}

.page-title {
    text-align: center;
    color: #2c5aa0;
    font-size: 36px;
    margin-bottom: 40px;
    font-weight: 600;
}

.team-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 25px;
    margin-bottom: 50px;
    place-content: center;
}

.team-member {
    background: white;
    border-radius: 15px;
    padding: 30px;
    box-shadow: 0 5px 20px rgba(0, 100, 200, 0.1);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}


.member-header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #e6f2ff;
}

.member-avatar {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2c5aa0 0%, #1e3d6f 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 24px;
    font-weight: bold;
    margin-right: 20px;
}

.member-info h3 {
    color: #2c5aa0;
    font-size: 20px;
    margin-bottom: 5px;
}

.member-role {
    color: #666;
    font-size: 16px;
    font-weight: 500;
}

.member-responsibilities {
    color: #333;
    line-height: 1.6;
}

.responsibilities-list {
    list-style: none;
    padding-left: 0;
}

.responsibilities-list li {
    border-bottom: 1px solid #f0f0f0;
    position: relative;
    padding-left: 20px;
}

.responsibilities-list li:before {
    content: "•";
    color: #2c5aa0;
    font-weight: bold;
    position: absolute;
    left: 0;
}

.responsibilities-list li:last-child {
    border-bottom: none;
}

.project-info {
    background: white;
    border-radius: 15px;
    padding: 25px;
    box-shadow: 0 5px 20px rgba(0, 100, 200, 0.1);
    margin-top: 30px;
}

.project-title {
    color: #2c5aa0;
    font-size: 24px;
    margin-bottom: 20px;
    text-align: center;
}

.project-description {
    color: #333;
    line-height: 1.6;
    text-align: center;
    max-width: 800px;
    margin: 0 auto;
}

@media (max-width: 768px) {
    .top-bar-content {
        flex-direction: column;
        gap: 10px;
        text-align: center;
    }

    .nav-links {
        gap: 15px;
    }

    .page-title {
        font-size: 28px;
        margin-bottom: 30px;
    }

    .team-container {
        grid-template-columns: 1fr;
        gap: 20px;
    }

    .team-member {
        padding: 20px;
    }

    .member-header {
        flex-direction: column;
        text-align: center;
    }

    .member-avatar {
        margin-right: 0;
        margin-bottom: 15px;
    }

    .project-info {
        padding: 20px;
    }
}

@media (max-width: 480px) {
    .top-bar {
        padding: 12px 0;
    }

    .image_logo {
        height: 35px;
    }

    .nav-links {
        flex-wrap: wrap;
        justify-content: center;
        gap: 10px;
    }

    .page-title {
        font-size: 24px;
    }

    .team-member {
        padding: 15px;
    }
}
</style>

<script>

</script>


