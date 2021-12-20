<template>
  <div>
    <h2 v-if="isMethodList">Methods</h2>
    <h2 v-else>Functions</h2>
    <div v-if="functions.length > 0">
      <div v-for="functionDef in functions" :key="functionDef.namespace">
        <NuxtLink :to="`/def/${functionDef.namespace}`">{{ functionDef.name }}</NuxtLink>
      </div>
    </div>
    <b-alert show v-else>
      {{ parentName }} has no function / method definitions.
    </b-alert>
  </div>
</template>

<script>
export default {
  name: 'FunctionList',
  props: {
    functions: {
      type: Array,
      required: true,
    },
    parentName: {
      type: String,
      required: true,
    },
    isMethodList: {
      type: Boolean,
    }
  }
}
</script>
