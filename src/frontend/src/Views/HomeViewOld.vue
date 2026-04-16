<template>
  <body :class="{'high-contrast-mode': isHighContrast}">
  <!-- Кнопка доступности -->
  <div class="accessibility-toggle">
    <button
        @click="toggleHighContrast"
        class="accessibility-btn"
        :title="isHighContrast ? 'Обычный режим' : 'Режим для слабовидящих'"
        @mouseenter="speak(isHighContrast ? 'Кнопка переключения в обычный режим' : 'Кнопка переключения в режим для слабовидящих')"
        @mouseleave="stopSpeech"
    >
      <span class="btn-icon">👁️</span>
      {{ isHighContrast ? 'Обычный вид' : 'Для слабовидящих' }}
    </button>
  </div>
  <div class="speech-toggle">
    <button
        @click="toggleSpeech"
        class="speech-btn"
        :title="speechEnabled ? 'Выключить озвучку' : 'Включить озвучку'"
        @mouseenter="speak(speechEnabled ? 'Кнопка выключения озвучки' : 'Кнопка включения озвучки')"
        @mouseleave="stopSpeech"
    >
      <span class="btn-icon">{{ speechEnabled ? '🔊' : '🔇' }}</span>
      {{ speechEnabled ? 'Озвучка ВКЛ' : 'Озвучка ВЫКЛ' }}
    </button>
  </div>

  <!-- Основной контент -->
  <div class="main-content">
    <div class="sidebar">
      <h3 class="sidebar-title"
          @mouseenter="speak('Последние запросы')"
          @mouseleave="stopSpeech">Последние запросы</h3>
      <ul class="history-list" id="historyList">
        <li v-for="(item, index) in history" :key="index" class="history-item"
            @click="openChatHistory(item)"
            @mouseenter="speak('Запрос: ' + item.query + '. Ответ: ' + getAnswerPreview(item.answer))"
            @mouseleave="stopSpeech">
          <div class="history-query">{{ item.query }}</div>
          <div class="history-answer-preview">{{ getAnswerPreview(item.answer) }}</div>
          <div class="history-meta">
            <span class="history-time">{{ formatTime(item.timestamp) }}</span>
            <span class="history-messages">{{ item.messages ? item.messages.length : 1 }} сообщ.</span>
          </div>
        </li>
        <li v-if="history.length === 0" class="empty-history"
            @mouseenter="speak('История запросов пуста')"
            @mouseleave="stopSpeech">История запросов пуста</li>
      </ul>
      <button type="button" class="search-button clear-button" @click="clearHistory" v-if="history.length > 0"
              @mouseenter="speak('Кнопка очистить историю')"
              @mouseleave="stopSpeech">
        Очистить историю
      </button>
    </div>

    <div class="search-container">
      <!-- Заголовок в зависимости от режима -->
      <h1 class="search-title"
          @mouseenter="speak(currentChatHistory ? 'Продолжение диалога' : 'Введите ваш запрос')"
          @mouseleave="stopSpeech">
        {{ currentChatHistory ? 'Продолжение диалога' : 'Введите ваш запрос' }}
      </h1>

      <!-- Кнопка возврата к новому запросу (показывается только в режиме продолжения диалога) -->
      <div v-if="currentChatHistory" class="chat-history-header">
        <button @click="closeChatHistory" class="search-button back-button"
                @mouseenter="speak('Вернуться к новому запросу')"
                @mouseleave="stopSpeech">
          ← Новый запрос
        </button>
        <div class="original-query">
          Исходный запрос: "{{ currentChatHistory.query }}"
        </div>
      </div>

      <!-- История текущего диалога -->
      <div v-if="currentChatHistory" class="chat-history">
        <div v-for="(message, index) in currentChatHistory.messages" :key="index"
             class="chat-message" :class="{'user-message': message.role === 'user', 'ai-message': message.role === 'assistant'}">
          <div class="message-role">{{ message.role === 'user' ? 'Вы' : 'Ассистент' }}</div>
          <div class="message-content">{{ message.content }}</div>
          <div class="message-time">{{ formatMessageTime(message.timestamp) }}</div>
        </div>
      </div>

      <!-- Новый селектор под заголовком -->
      <div class="query-type-selector">
        <label for="queryType" class="query-type-label"
               @mouseenter="speak('Выбор роли')"
               @mouseleave="stopSpeech">Роль:</label>
        <select
            id="queryType"
            class="query-type-select"
            v-model="selectedQueryType"
            @change="onQueryTypeChange"
            @mouseenter="speak('Выберите роль для поиска')"
            @mouseleave="stopSpeech"
            @focus="speak('Выбор роли. Текущая роль: ' + getRoleName(selectedQueryType))"
        >
          <option value="student">Студент</option>
          <option value="programmist">Программист</option>
          <option value="kolhoznik">Глава сельского поселения</option>
        </select>
      </div>

      <form class="search-form" id="searchForm" @submit.prevent="handleSearch">
        <input type="text" class="search-input" placeholder="Введите запрос" required id="searchInput"
               v-model="searchQuery"
               @mouseenter="speak('Поле для ввода запроса')"
               @mouseleave="stopSpeech"
               @focus="speak('Введите ваш запрос в это поле')">
        <div class="button-group">
          <button type="submit" class="search-button" :disabled="loading"
                  @mouseenter="speak(loading ? 'Идет поиск' : 'Кнопка найти')"
                  @mouseleave="stopSpeech">
            {{ loading ? 'Поиск...' : currentChatHistory ? 'Продолжить' : 'Найти' }}
          </button>
          <button type="button" class="search-button" id="uploadButton"
                  @click="openUploadDialog"
                  @mouseenter="speak('Кнопка загрузить файл')"
                  @mouseleave="stopSpeech">Загрузить файл</button>
          <button type="button" class="search-button_new" id="newRequestButton"
                  @click="newRequest"
                  @mouseenter="speak('Кнопка новый запрос')"
                  @mouseleave="stopSpeech">Новый запрос</button>
        </div>
      </form>

      <!-- Лоадер -->
      <div class="loader-container" style="display: none;">
        <div class="loader"></div>
      </div>

      <!-- Результаты поиска (только для новых запросов) -->
      <div v-if="searchResult && !currentChatHistory" class="results-container"
           @mouseenter="speakResult()"
           @mouseleave="stopSpeech">
        <div class="result-card">
          <h3 class="result-title">Ответ:</h3>
          <p class="result-text">{{ searchResult.answer }}</p>
          <div class="result-meta">
            <span class="processing-time">Время обработки: {{ searchResult.processing_time }} сек</span>
            <span class="sources">Источники: {{ searchResult.sources.join(', ') }}</span>
          </div>
        </div>
      </div>

      <!-- Сообщение об ошибке -->
      <div v-if="error" class="error-message"
           @mouseenter="speak('Ошибка: ' + error)"
           @mouseleave="stopSpeech">
        {{ error }}
      </div>
    </div>

    <!-- Модальное окно загрузки файла -->
    <div v-if="showUploadDialog" class="modal-overlay" @click="closeUploadDialog">
      <div class="modal-content" @click.stop>
        <h3 @mouseenter="speak('Загрузка документа')"
            @mouseleave="stopSpeech">Загрузка документа</h3>
        <input type="file" ref="fileInput" @change="handleFileSelect" accept=".pdf,.docx,.txt"
               @mouseenter="speak('Выберите файл для загрузки')"
               @mouseleave="stopSpeech">
        <div class="modal-buttons">
          <button @click="uploadDocument" :disabled="uploading" class="search-button"
                  @mouseenter="speak(uploading ? 'Идет загрузка файла' : 'Кнопка загрузить файл')"
                  @mouseleave="stopSpeech">
            {{ uploading ? 'Загрузка...' : 'Загрузить' }}
          </button>
          <button @click="closeUploadDialog" class="search-button cancel-button"
                  @mouseenter="speak('Кнопка отмена')"
                  @mouseleave="stopSpeech">Отмена</button>
        </div>
        <div class="loader-container" id="load_loader" style="display: none;">
          <div class="loader"></div>
        </div>
        <div v-if="uploadResult" class="upload-result"
             @mouseenter="speak(uploadResult.message)"
             @mouseleave="stopSpeech">
          {{ uploadResult.message }}
        </div>
      </div>
    </div>
  </div>
  </body>
</template>

<style scoped>
/* Существующие стили остаются без изменений, добавляем только стили для переключателя озвучки */

.speech-toggle {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 1000;
}

.speech-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 25px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  font-family: 'Arial', sans-serif;
}

.speech-btn:hover {
  background: #218838;
  transform: translateY(-2px);
}

body.high-contrast-mode .speech-btn {
  background: #ffffff !important;
  color: #000000 !important;
  border: 2px solid #ffffff !important;
  font-weight: bold !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .speech-btn:hover {
  background: #cccccc !important;
  color: #000000 !important;
  border-color: #cccccc !important;
}

/* Стили для результатов поиска и ошибок */
.results-container {
  margin-top: 30px;
  text-align: left;
}

.result-card {
  background: #f8fbff;
  border: 1px solid #e6f2ff;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 3px 10px rgba(0, 100, 200, 0.1);
}

.result-title {
  color: #2c5aa0;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 15px;
}

.result-text {
  color: #333;
  line-height: 1.6;
  margin-bottom: 15px;
  font-size: 15px;
  white-space: pre-line;
}

.result-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #666;
  border-top: 1px solid #e6f2ff;
  padding-top: 15px;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 15px;
  border-radius: 8px;
  margin-top: 20px;
  border: 1px solid #f5c6cb;
}

/* Модальное окно */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  min-width: 400px;
  text-align: center;
}

.modal-content h3 {
  color: #2c5aa0;
  margin-bottom: 20px;
}

.modal-content input[type="file"] {
  width: 100%;
  padding: 10px;
  margin-bottom: 20px;
  border: 2px dashed #e6f2ff;
  border-radius: 8px;
}

.modal-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.upload-result {
  margin-top: 15px;
  padding: 10px;
  background: #d1edff;
  border-radius: 6px;
  color: #2c5aa0;
}

/* Стили для режима высокой контрастности */
body.high-contrast-mode .results-container .result-card {
  background: #000000 !important;
  border: 3px solid #ffffff !important;
  color: #ffffff !important;
}

body.high-contrast-mode .result-title {
  color: #ffffff !important;
  font-size: 20px !important;
}

body.high-contrast-mode .result-text {
  color: #ffffff !important;
  font-size: 16px !important;
}

body.high-contrast-mode .result-meta {
  color: #cccccc !important;
  border-top: 2px solid #ffffff !important;
}

body.high-contrast-mode .error-message {
  background: #000000 !important;
  color: #ff4444 !important;
  border: 2px solid #ff4444 !important;
}

body.high-contrast-mode .modal-content {
  background: #000000 !important;
  border: 3px solid #ffffff !important;
  color: #ffffff !important;
}

body.high-contrast-mode .modal-content h3 {
  color: #ffffff !important;
}

body.high-contrast-mode .modal-content input[type="file"] {
  background: #000000 !important;
  border: 2px solid #ffffff !important;
  color: #ffffff !important;
}

body.high-contrast-mode .upload-result {
  background: #000000 !important;
  border: 2px solid #ffffff !important;
  color: #ffffff !important;
}

/* Адаптивность для переключателей */
@media (max-width: 768px) {
  .speech-toggle {
    position: relative;
    top: auto;
    right: auto;
    text-align: center;
    margin-bottom: 10px;
  }

  .speech-btn {
    padding: 10px 16px;
    font-size: 13px;
  }
}

/* Стили для лоадера */
.loader-container {
  display: none;
  justify-content: center;
  align-items: center;
  margin: 20px 0;
}

.loader {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #2c5aa0;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.clear-button {
  background: #dc3545;
  margin-top: 15px;
  width: 100%;
}

.clear-button:hover:not(:disabled) {
  background: #c82333;
}

/* Остальные существующие стили остаются без изменений */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Arial', sans-serif;
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, font-family 0.3s ease;
}

@font-face {
  font-family: 'LucidaSansUnicode';
  src: url('../assets/fonts/lucidasansunicode.ttf') format('truetype');
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}

body {
  background: linear-gradient(135deg, #e6f2ff 0%, #ffffff 100%);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Контейнер для селектора ролей */
.role-selector-container {
  width: 100%;
  background: linear-gradient(135deg, #f8fbff 0%, #e6f2ff 100%);
  border-bottom: 2px solid #e6f2ff;
  padding: 15px 0;
  margin-top: 80px; /* Отступ для кнопки доступности */
}

.role-selector-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  margin-top: -5%;
  margin-right: 3%;
}

.role-selector {
  display: flex;
  align-items: center;
  gap: 15px;
  background: white;
  padding: 15px 20px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 100, 200, 0.1);
  border: 2px solid #e6f2ff;
  max-width: 400px;
  margin: 0 auto;
}

.role-label {
  font-weight: 600;
  color: #2c5aa0;
  font-size: 16px;
  white-space: nowrap;
  font-family: 'Arial', sans-serif;
}

.role-select {
  flex: 1;
  padding: 10px 15px;
  border: 2px solid #e6f2ff;
  border-radius: 8px;
  font-size: 15px;
  background: white;
  color: #333;
  cursor: pointer;
  outline: none;
  transition: all 0.3s ease;
  font-family: 'Arial', sans-serif;
}

.role-select:focus {
  border-color: #2c5aa0;
  box-shadow: 0 0 0 3px rgba(44, 90, 160, 0.1);
}

.role-select:hover {
  border-color: #2c5aa0;
}

/* Новый селектор типа запроса */
.query-type-selector {
  display: flex;
  align-items: center;
  gap: 15px;
  background: white;
  padding: 15px 20px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 100, 200, 0.1);
  border: 2px solid #e6f2ff;
  max-width: 400px;
  margin: 0 auto 25px auto;
  justify-content: center;
}

.query-type-label {
  font-weight: 600;
  color: #2c5aa0;
  font-size: 16px;
  white-space: nowrap;
  font-family: 'Arial', sans-serif;
}

.query-type-select {
  flex: 1;
  padding: 10px 15px;
  border: 2px solid #e6f2ff;
  border-radius: 8px;
  font-size: 15px;
  background: white;
  color: #333;
  cursor: pointer;
  outline: none;
  transition: all 0.3s ease;
  font-family: 'Arial', sans-serif;
  min-width: 200px;
}

.query-type-select:focus {
  border-color: #2c5aa0;
  box-shadow: 0 0 0 3px rgba(44, 90, 160, 0.1);
}

.query-type-select:hover {
  border-color: #2c5aa0;
}

/* Стили для режима высокой контрастности */
body.high-contrast-mode .role-selector-container {
  background: #000000 !important;
  border-bottom: 3px solid #ffffff !important;
}

body.high-contrast-mode .role-selector {
  background: #000000 !important;
  border: 3px solid #ffffff !important;
  color: #ffffff !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .role-label {
  color: #ffffff !important;
  font-size: 18px !important;
  font-weight: bold !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .role-select {
  background: #000000 !important;
  border: 2px solid #ffffff !important;
  color: #ffffff !important;
  font-size: 16px !important;
  font-weight: bold !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .role-select option {
  background: #000000 !important;
  color: #ffffff !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

/* Стили для селектора типа запроса в режиме высокой контрастности */
body.high-contrast-mode .query-type-selector {
  background: #000000 !important;
  border: 3px solid #ffffff !important;
  color: #ffffff !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .query-type-label {
  color: #ffffff !important;
  font-size: 18px !important;
  font-weight: bold !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .query-type-select {
  background: #000000 !important;
  border: 2px solid #ffffff !important;
  color: #ffffff !important;
  font-size: 16px !important;
  font-weight: bold !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .query-type-select option {
  background: #000000 !important;
  color: #ffffff !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

/* Остальные стили остаются такими же, но с небольшими корректировками */
body.high-contrast-mode {
  background: #000000 !important;
  color: #ffffff !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .main-content {
  background: transparent;
}

body.high-contrast-mode .sidebar {
  background: #000000 !important;
  border: 3px solid #ffffff !important;
  color: #ffffff !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .sidebar-title {
  color: #ffffff !important;
  border-bottom: 3px solid #ffffff !important;
  font-size: 22px !important;
  font-weight: bold !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .history-item {
  background: #000000 !important;
  border: 2px solid #ffffff !important;
  color: #ffffff !important;
  font-size: 16px !important;
  font-weight: bold !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .history-item:hover {
  background: #333333 !important;
  border-color: #cccccc !important;
}

body.high-contrast-mode .search-container {
  background: #000000 !important;
  border: 3px solid #ffffff !important;
  color: #ffffff !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .search-title {
  color: #ffffff !important;
  font-size: 28px !important;
  font-weight: bold !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .search-input {
  background: #000000 !important;
  border: 3px solid #ffffff !important;
  color: #ffffff !important;
  font-size: 18px !important;
  font-weight: bold !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .search-input::placeholder {
  color: #cccccc !important;
  font-size: 18px !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .search-input:focus {
  border-color: #ffffff !important;
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.3) !important;
  background: #1a1a1a !important;
}

body.high-contrast-mode .search-button {
  background: #ffffff !important;
  color: #000000 !important;
  border: 2px solid #ffffff !important;
  font-size: 18px !important;
  font-weight: bold !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .search-button:hover {
  background: #cccccc !important;
  color: #000000 !important;
  border-color: #cccccc !important;
}

.accessibility-toggle {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
}

.accessibility-btn {
  background: #2c5aa0;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 25px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  font-family: 'Arial', sans-serif;
}

.accessibility-btn:hover {
  background: #1e3d6f;
  transform: translateY(-2px);
}

body.high-contrast-mode .accessibility-btn {
  background: #ffffff !important;
  color: #000000 !important;
  border: 2px solid #ffffff !important;
  font-weight: bold !important;
  font-family: 'LucidaSansUnicode', 'Arial', sans-serif !important;
}

body.high-contrast-mode .accessibility-btn:hover {
  background: #cccccc !important;
  color: #000000 !important;
  border-color: #cccccc !important;
}

.btn-icon {
  font-size: 16px;
}

.main-content {
  flex: 1;
  display: flex;
  max-width: 1200px;
  margin: 20px auto 0;
  width: 100%;
  padding: 40px 20px;
  gap: 30px;
}

.sidebar {
  width: 300px;
  background: white;
  border-radius: 15px;
  box-shadow: 0 5px 20px rgba(0, 100, 200, 0.1);
  padding: 25px;
  height: fit-content;
  font-family: 'Arial', sans-serif;
}

.sidebar-title {
  color: #2c5aa0;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e6f2ff;
  font-family: 'Arial', sans-serif;
}

.history-list {
  list-style: none;
}

.history-item {
  padding: 12px 15px;
  margin-bottom: 8px;
  background: #f8fbff;
  border: 1px solid #e6f2ff;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #333;
  font-size: 14px;
  font-family: 'Arial', sans-serif;
}

.history-item:hover {
  background: #e6f2ff;
  border-color: #2c5aa0;
  transform: translateX(5px);
}

.history-item:last-child {
  margin-bottom: 0;
}

.empty-history {
  color: #999;
  font-style: italic;
  text-align: center;
  padding: 20px 0;
  font-family: 'Arial', sans-serif;
}

.search-container {
  background: white;
  padding: 40px;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 100, 200, 0.1);
  flex: 1;
  text-align: center;
  font-family: 'Arial', sans-serif;
}

.search-title {
  color: #2c5aa0;
  font-size: 24px;
  margin-bottom: 30px;
  font-weight: 600;
  font-family: 'Arial', sans-serif;
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-input {
  padding: 15px 20px;
  border: 2px solid #e6f2ff;
  border-radius: 12px;
  font-size: 16px;
  outline: none;
  transition: all 0.3s ease;
  color: #333;
  font-family: 'Arial', sans-serif;
}

.search-input:focus {
  border-color: #2c5aa0;
  box-shadow: 0 0 0 3px rgba(44, 90, 160, 0.1);
}

.search-input::placeholder {
  color: #999;
  font-family: 'Arial', sans-serif;
}

.search-button_new {
  background: #ea3263;
  color: white;
  border: none;
  padding: 15px 30px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Arial', sans-serif;
}

.search-button {
  background: #2c5aa0;
  color: white;
  border: none;
  padding: 15px 30px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Arial', sans-serif;
}

.search-button:hover:not(:disabled) {
  background: #1e3d6f;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(44, 90, 160, 0.3);
}

.search-button:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}

.search-button_new:hover {
  background: #d12a55;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(234, 50, 99, 0.3);
}

.search-button:active:not(:disabled) {
  transform: translateY(0);
}

.button-group {
  display: flex;
  gap: 15px;
}

.button-group .search-button {
  flex: 1;
}

/* Адаптивность */
@media (max-width: 768px) {
  .accessibility-toggle {
    position: relative;
    top: auto;
    right: auto;
    text-align: center;
    margin-bottom: 20px;
  }

  .accessibility-btn {
    padding: 10px 16px;
    font-size: 13px;
  }

  .role-selector-container {
    margin-top: 0;
    padding: 10px 0;
  }

  .role-selector {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    max-width: 100%;
  }

  .role-label {
    text-align: center;
  }

  .query-type-selector {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    max-width: 100%;
    margin-bottom: 20px;
  }

  .query-type-label {
    text-align: center;
  }

  .main-content {
    flex-direction: column;
    padding: 20px;
    margin-top: 10px;
  }

  .sidebar {
    width: 100%;
    order: 2;
  }

  .search-container {
    order: 1;
    padding: 30px 25px;
  }

  .search-title {
    font-size: 20px;
    margin-bottom: 25px;
  }

  .search-input {
    padding: 12px 18px;
    font-size: 15px;
  }

  .search-button {
    padding: 12px 25px;
    font-size: 15px;
  }

  .button-group {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .role-selector {
    padding: 12px 15px;
  }

  .role-label {
    font-size: 14px;
  }

  .role-select {
    padding: 8px 12px;
    font-size: 14px;
  }

  .query-type-selector {
    padding: 12px 15px;
  }

  .query-type-label {
    font-size: 14px;
  }

  .query-type-select {
    padding: 8px 12px;
    font-size: 14px;
    min-width: 150px;
  }

  .search-container {
    padding: 25px 20px;
  }

  .search-title {
    font-size: 18px;
    margin-bottom: 20px;
  }

  .search-form {
    gap: 15px;
  }

  .sidebar {
    padding: 20px;
  }
}

.chat-history-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8fbff;
  border-radius: 12px;
  border: 1px solid #e6f2ff;
}

.back-button {
  background: #6c757d;
  padding: 10px 20px;
  font-size: 14px;
}

.back-button:hover {
  background: #5a6268;
}

.original-query {
  color: #2c5aa0;
  font-weight: 600;
  font-size: 16px;
}

.chat-history {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 20px;
  border: 1px solid #e6f2ff;
  border-radius: 12px;
  padding: 15px;
  background: #fafafa;
}

.chat-message {
  margin-bottom: 15px;
  padding: 12px 15px;
  border-radius: 8px;
  position: relative;
}

.user-message {
  background: #e6f2ff;
  border-left: 4px solid #2c5aa0;
  margin-left: 20px;
}

.ai-message {
  background: #f0f8ff;
  border-left: 4px solid #28a745;
  margin-right: 20px;
}

.message-role {
  font-weight: 600;
  font-size: 14px;
  color: #2c5aa0;
  margin-bottom: 5px;
}

.message-content {
  color: #333;
  line-height: 1.5;
  white-space: pre-line;
}

.message-time {
  font-size: 12px;
  color: #666;
  text-align: right;
  margin-top: 5px;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.history-time {
  font-style: italic;
}

.history-messages {
  background: #e6f2ff;
  padding: 2px 6px;
  border-radius: 10px;
}

/* Стили для режима высокой контрастности */
body.high-contrast-mode .chat-history-header {
  background: #000000 !important;
  border: 2px solid #ffffff !important;
}

body.high-contrast-mode .original-query {
  color: #ffffff !important;
}

body.high-contrast-mode .chat-history {
  background: #000000 !important;
  border: 2px solid #ffffff !important;
}

body.high-contrast-mode .user-message {
  background: #1a1a1a !important;
  border-left: 4px solid #ffffff !important;
}

body.high-contrast-mode .ai-message {
  background: #2a2a2a !important;
  border-left: 4px solid #cccccc !important;
}

body.high-contrast-mode .message-role {
  color: #ffffff !important;
}

body.high-contrast-mode .message-content {
  color: #ffffff !important;
}

body.high-contrast-mode .message-time {
  color: #cccccc !important;
}

body.high-contrast-mode .history-messages {
  background: #ffffff !important;
  color: #000000 !important;
}
</style>

<script>
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default {
  name: 'RAGSearch',
  data() {
    return {
      searchQuery: '',
      searchResult: null,
      history: [],
      loading: false,
      error: null,
      showUploadDialog: false,
      selectedFile: null,
      uploading: false,
      uploadResult: null,
      isHighContrast: false,
      selectedQueryType: 'student',
      speechEnabled: true,
      currentChatHistory: null // Текущая открытая история диалога
    }
  },
  mounted() {
    this.loadHistory();
    const savedMode = localStorage.getItem('highContrastMode');
    if (savedMode !== null) {
      this.isHighContrast = savedMode === 'true';
    }
    const savedSpeech = localStorage.getItem('speechEnabled');
    if (savedSpeech !== null) {
      this.speechEnabled = savedSpeech === 'true';
    }
  },
  methods: {
    // Функции озвучки
    speak(text) {
      if (!this.speechEnabled) return;
      if ('speechSynthesis' in window) {
        speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.lang = 'ru-RU';

        const voices = speechSynthesis.getVoices();
        const russianVoice = voices.find(voice =>
            voice.lang.includes('ru') || voice.lang.includes('RU')
        );
        if (russianVoice) {
          utterance.voice = russianVoice;
        }

        speechSynthesis.speak(utterance);
      }
    },

    speakResult() {
      if (!this.speechEnabled || !this.searchResult) return;
      const resultText = `Ответ: ${this.searchResult.answer}. Время обработки: ${this.searchResult.processing_time} секунд. Источники: ${this.searchResult.sources.join(', ')}`;
      this.speak(resultText);
    },

    stopSpeech() {
      if (this.speechEnabled) {
        speechSynthesis.cancel();
      }
    },

    toggleSpeech() {
      this.speechEnabled = !this.speechEnabled;
      this.stopSpeech();
      localStorage.setItem('speechEnabled', this.speechEnabled);
    },

    getRoleName(role) {
      const roles = {
        'student': 'Студент',
        'programmist': 'Программист',
        'kolhoznik': 'Глава сельского поселения'
      };
      return roles[role] || role;
    },

    // Функции доступности
    toggleHighContrast() {
      this.isHighContrast = !this.isHighContrast;
      localStorage.setItem('highContrastMode', this.isHighContrast);
    },

    onQueryTypeChange() {
      const roleName = this.getRoleName(this.selectedQueryType);
      this.speak(`Выбрана роль: ${roleName}`);
      console.log('Выбран тип запроса:', this.selectedQueryType);
    },

    newRequest() {
      this.searchQuery = '';
      this.searchResult = null;
      this.error = null;
      this.currentChatHistory = null;
      this.speak("Новый запрос. Поле очищено");
    },

    // Основные функции поиска
    async handleSearch() {
      if (!this.searchQuery.trim()) {
        this.speak("Пожалуйста, введите запрос");
        return;
      }

      this.loading = true;
      this.error = null;

      // Для новых запросов очищаем результат, для продолжения диалога - нет
      if (!this.currentChatHistory) {
        this.searchResult = null;
      }

      const loader_container = document.querySelector(".loader-container");

      try {
        loader_container.style.display = "flex";
        this.speak(this.currentChatHistory ? "Продолжаем диалог..." : "Идет поиск...");

        // Подготавливаем историю чата для API
        // Подготавливаем историю чата для API
        let chatHistory = [];
        let finalQuery = this.searchQuery;

        if (this.currentChatHistory && this.currentChatHistory.messages) {
          chatHistory = this.currentChatHistory.messages.map(msg => ({
            role: msg.role,
            content: msg.content
          }));
          
          // Если это не первый вопрос в диалоге, добавляем контекст
          const userMessages = chatHistory.filter(msg => msg.role === 'user');
          if (userMessages.length > 0) {
            const lastUserQuestion = userMessages[userMessages.length - 1].content;
            const lastAssistantAnswer = chatHistory[chatHistory.length - 1].content;
            
            // Формируем уточняющий вопрос с контекстом
            finalQuery = `В контексте предыдущего общения:
        Предыдущий вопрос: "${lastUserQuestion}"
        Предыдущий ответ: "${lastAssistantAnswer}"

        Текущий уточняющий вопрос: ${this.searchQuery}

        Ответь с учётом этого контекста.`;
          }
        }

        const response = await axios.post(`${API_BASE_URL}/search`, {
          query: finalQuery,
          role: this.getApiRole(this.selectedQueryType),
          chat_history: chatHistory
        });

        this.searchResult = response.data;

        // Сохраняем в историю (остальной код без изменений)
        if (this.currentChatHistory) {
          this.currentChatHistory.messages.push(
            { role: 'user', content: this.searchQuery, timestamp: new Date().toISOString() },
            { role: 'assistant', content: this.searchResult.answer, timestamp: new Date().toISOString() },
          );
          this.updateHistoryItem(this.currentChatHistory);
        } else {
          const newHistoryItem = {
            query: this.searchQuery,
            answer: this.searchResult.answer,
            processing_time: this.searchResult.processing_time,
            timestamp: new Date().toISOString(),
            messages: [
              { role: 'user', content: this.searchQuery, timestamp: new Date().toISOString() },
              { role: 'assistant', content: this.searchResult.answer, timestamp: new Date().toISOString() }
            ]
          };
          this.addToHistory(newHistoryItem);
      }


        // Очищаем поле ввода после успешного запроса
        this.searchQuery = '';

        this.speak(this.currentChatHistory ? "Ответ получен" : "Поиск завершен");

      } catch (error) {
        console.error('Ошибка поиска:', error);
        this.error = error.response?.data?.detail || 'Произошла ошибка при поиске';
        this.speak("Произошла ошибка при поиске");
      } finally {
        this.loading = false;
        loader_container.style.display = "none";
      }
    },

    // Методы для работы с историей диалога
    openChatHistory(item) {
      this.currentChatHistory = { ...item };
      this.searchQuery = '';
      this.searchResult = null;
      this.error = null;
      this.speak(`Открыта история диалога. Исходный запрос: ${item.query}. Всего сообщений: ${item.messages ? item.messages.length : 1}`);

      // Прокручиваем к началу формы
      this.$nextTick(() => {
        const searchForm = this.$el.querySelector('.search-form');
        if (searchForm) {
          searchForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    },

    closeChatHistory() {
      this.currentChatHistory = null;
      this.searchQuery = '';
      this.searchResult = null;
      this.error = null;
      this.speak("Режим нового запроса");
    },

    // Вспомогательные методы
    getApiRole(frontendRole) {
      const roleMap = {
        'student': 'студент',
        'programmist': 'программист',
        'kolhoznik': 'глава'
      };
      return roleMap[frontendRole] || 'студент';
    },

    formatTime(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleDateString('ru-RU') + ' ' + date.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    formatMessageTime(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    addToHistory(searchItem) {
      // Убедимся, что у элемента есть массив messages
      if (!searchItem.messages) {
        searchItem.messages = [
          { role: 'user', content: searchItem.query, timestamp: searchItem.timestamp },
          { role: 'assistant', content: searchItem.answer, timestamp: searchItem.timestamp }
        ];
      }

      this.history = this.history.filter(item => item.timestamp !== searchItem.timestamp);
      this.history.unshift(searchItem);

      if (this.history.length > 15) {
        this.history = this.history.slice(0, 15);
      }

      this.saveHistory();
    },

    updateHistoryItem(updatedItem) {
      const index = this.history.findIndex(item => item.timestamp === updatedItem.timestamp);
      if (index !== -1) {
        this.history[index] = updatedItem;
        this.saveHistory();
      }
    },

    getAnswerPreview(answer) {
      if (!answer) return '';
      const preview = answer.length > 100 ? answer.substring(0, 100) + '...' : answer;
      return preview;
    },

    loadHistory() {
      const saved = localStorage.getItem('rag-search-history');
      if (saved) {
        try {
          this.history = JSON.parse(saved);
          // Миграция старых записей без messages
          this.history.forEach(item => {
            if (!item.messages) {
              item.messages = [
                { role: 'user', content: item.query, timestamp: item.timestamp },
                { role: 'assistant', content: item.answer, timestamp: item.timestamp }
              ];
            }
          });
          this.saveHistory(); // Сохраняем обновленную историю
        } catch (e) {
          console.error('Ошибка загрузки истории:', e);
          this.history = [];
        }
      }
    },

    saveHistory() {
      localStorage.setItem('rag-search-history', JSON.stringify(this.history));
    },

    clearHistory() {
      if (confirm('Вы уверены, что хотите очистить историю поиска?')) {
        this.history = [];
        this.currentChatHistory = null;
        localStorage.removeItem('rag-search-history');
        this.speak("История очищена");
      }
    },

    openUploadDialog() {
      this.showUploadDialog = true;
      this.uploadResult = null;
      this.selectedFile = null;
      this.speak("Открыто окно загрузки файла");
    },

    closeUploadDialog() {
      this.showUploadDialog = false;
      this.selectedFile = null;
      this.uploadResult = null;
      this.stopSpeech();
    },

    handleFileSelect(event) {
      this.selectedFile = event.target.files[0];
      if (this.selectedFile) {
        this.speak(`Выбран файл: ${this.selectedFile.name}`);
      }
    },

    async uploadDocument() {
      if (!this.selectedFile) {
        this.speak("Пожалуйста, выберите файл");
        return;
      }

      this.uploading = true;
      this.uploadResult = null;
      const loader_container = document.querySelector("#load_loader");

      try {
        loader_container.style.display = "flex";
        this.speak("Начинается загрузка файла");

        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('role', this.getApiRole(this.selectedQueryType));

        const response = await axios.post(`${API_BASE_URL}/upload`, formData);

        this.uploadResult = response.data;
        this.selectedFile = null;

        // Очищаем поле файла
        if (this.$refs.fileInput) {
          this.$refs.fileInput.value = '';
        }

        this.speak("Файл успешно загружен");

        // Закрываем диалог через 2 секунды после успешной загрузки
        setTimeout(() => {
          this.closeUploadDialog();
        }, 2000);

      } catch (error) {
        console.error('Ошибка загрузки:', error);
        this.uploadResult = {
          message: error.response?.data?.detail || 'Произошла ошибка при загрузке файла'
        };
        this.speak("Произошла ошибка при загрузке файла");
      } finally {
        this.uploading = false;
        loader_container.style.display = "none";
      }
    }
  }
}
</script>
