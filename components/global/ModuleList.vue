<template>
  <div>
    <h2>Modules</h2>
    <div v-if="modules.length > 0">
      <div v-for="mod in modules" :key="mod.namespace">
        <NuxtLink :to="`/mod/${mod.namespace}`">{{ mod.namespace }}</NuxtLink>
      </div>
    </div>
    <b-alert show v-else>
      {{ packageName }} has no direct submodules.
    </b-alert>
  </div>
</template>

<script>
export default {
  name: 'ModuleList',
  props: {
    modules: {
      type: Array,
      required: true
    },
    packageName: {
      type: String,
      required: true
    }
  }
}
</script>
