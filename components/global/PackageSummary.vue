<template>
  <div>
    <NuxtLink :to="`/pkg/${pkg.name}`">{{ pkg.name }}</NuxtLink>
  </div>
</template>

<script>
export default {
  name: 'PackageSummary',
  props: {
    pkg: {
      type: Object,
      required: true
    }
  }
}
</script>
