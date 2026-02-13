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
    <AccountInput label="Счёт списания" :placeholder="'Выберите счёт списания'" />
    <AccountInput label="Категория" :placeholder="'Выберите категорию'" />
    <TagsInput />
    <CommentInput />
    <AppButton button-text="Создать расход" />
  </form>
</template>
