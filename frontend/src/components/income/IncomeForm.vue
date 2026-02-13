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
    <AccountInput label="Счет зачисления" :placeholder="'Выберите счет зачисления'" />
    <AccountInput label="Источник дохода" :placeholder="'Выберите источник дохода'" />
    <TagsInput />
    <CommentInput />
    <AppButton button-text="Создать доход" />
  </form>
</template>
