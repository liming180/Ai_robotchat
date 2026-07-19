<template>
  <div class="chat-input-container">
    <div class="input-wrapper">
      <textarea
        v-model="message"
        @input="adjustHeight"
        @keydown.enter="handleSendMessage"
        placeholder="输入消息..."
        rows="1"
        class="chat-textarea"
      />
      <div class="input-actions">
        <button class="emoji-btn" @click="toggleEmojiPicker">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-5h2v2h-2zm0-4h2v2h-2z"/>
          </svg>
        </button>
        <button class="image-btn" @click="selectImage">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-5h2v2h-2zm0-4h2v2h-2z"/>
          </svg>
        </button>
        <button class="send-btn" @click="handleSendMessage">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Emoji Picker -->
    <div v-if="showEmojiPicker" class="emoji-picker">
      <div class="emoji-grid">
        <span
          v-for="emoji in emojiList"
          :key="emoji"
          @click="selectEmoji(emoji)"
          class="emoji-item"
        >
          {{ emoji }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
const message = ref('')
const showEmojiPicker = ref(false)

const emojiList = computed(() => {
  return ['😊', '😢', '😠', '😰', '😐', '❤️', '👍', '👎', '🎉', '🔥', '⭐', '🚀', '🌟']
})

const adjustHeight = () => {
  const textarea = document.querySelector('.chat-textarea') as HTMLTextAreaElement
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = `${textarea.scrollHeight}px`
  }
}

const handleSendMessage = () => {
  if (message.value.trim()) {
    chatStore.sendMessage(message.value)
    message.value = ''
    adjustHeight()
  }
}

const toggleEmojiPicker = () => {
  showEmojiPicker.value = !showEmojiPicker.value
}

const selectEmoji = (emoji: string) => {
  message.value += emoji
  showEmojiPicker.value = false
  adjustHeight()
}

const selectImage = () => {
  // Image selection logic
  console.log('Image selection triggered')
}

// Auto-adjust height on mount
onMounted(() => {
  adjustHeight()
})
</script>

<style scoped>
.chat-input-container {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1rem;
  z-index: 50;
}

.input-wrapper {
  display: flex;
  gap: 0.5rem;
  max-width: 800px;
  margin: 0 auto;
}

.chat-textarea {
  flex: 1;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 1rem;
  padding: 0.75rem 1rem;
  color: white;
  resize: none;
  font-size: 1rem;
  outline: none;
  transition: all 0.2s;
}

.chat-textarea:focus {
  border-color: rgba(168, 85, 247, 0.5);
  box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.2);
}

.input-actions {
  display: flex;
  gap: 0.5rem;
}

.emoji-btn, .image-btn, .send-btn {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.emoji-btn:hover, .image-btn:hover, .send-btn:hover {
  background: rgba(51, 65, 85, 0.5);
  border-color: rgba(168, 85, 247, 0.5);
}

.send-btn {
  background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
  border: none;
}

.send-btn:hover {
  background: linear-gradient(135deg, #db2777 0%, #7c3aed 100%);
}

.emoji-picker {
  position: absolute;
  bottom: 4rem;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 1rem;
  padding: 0.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  max-width: 300px;
}

.emoji-item {
  cursor: pointer;
  font-size: 1.25rem;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: all 0.2s;
}

.emoji-item:hover {
  background: rgba(51, 65, 85, 0.5);
}
</style>