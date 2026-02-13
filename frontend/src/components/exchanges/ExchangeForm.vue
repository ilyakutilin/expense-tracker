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
    <AmountInput label="Сумма продажи" />
    <AccountInput label="Счёт списания" :placeholder="'Выберите счёт списания'" />
    <AmountInput label="Сумма покупки" />
    <AccountInput label="Счёт зачисления" :placeholder="'Выберите счёт зачисления'" />
    <TagsInput />
    <CommentInput />
    <AppButton button-text="Создать обмен" />
  </form>
</template>
