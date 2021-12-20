<template>
  <div>
    <h2>Classes</h2>
    <div v-if="classes.length > 0">
      <div v-for="cls in classes" :key="cls.namespace">
        <NuxtLink :to="`/cls/${cls.namespace}`">{{ cls.name }}</NuxtLink>
      </div>
    </div>
    <b-alert show v-else>
      {{ parentName }} has no class definitions.
    </b-alert>
  </div>
</template>

<script>
export default {
  name: 'ClassList',
  props: {
    classes: {
      type: Array,
      required: true
    },
    parentName: {
      type: String,
      required: true,
    }
  }
}
</script>
