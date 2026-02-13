<script setup lang="ts">
import AppButton from '../common/AppButton.vue'
import AccountInput from '../common/input/AccountInput.vue'
import AmountInput from '../common/input/AmountInput.vue'
import CommentInput from '../common/input/CommentInput.vue'
import DateSelector from '../common/input/DateSelector.vue'
import TagsInput from '../common/input/TagsInput.vue'
import TemplateInput from '../common/input/TemplateInput.vue'
</script>
<template>
  <form>
    <DateSelector />
    <TemplateInput />
    <AmountInput />
    <AccountInput label="Переместить из" :placeholder="'Выберите счёт списания'" />
    <AccountInput label="Переместить в" :placeholder="'Выберите счёт зачисления'" />
    <TagsInput />
    <CommentInput />
    <AppButton button-text="Создать перемещение" />
  </form>
</template>
