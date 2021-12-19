<template>
  <div>
    <div v-for="pkg in content.packages" :key="pkg.name">
      <NuxtLink :to="`pkg/${pkg.name}`">{{ pkg.name }}</NuxtLink>
    </div>
  </div>
</template>

<script>
export default {
  name: 'IndexPage',

  asyncData: async ({ $content }) => {
    const content = await $content("library").fetch();
    return { content };
  }
}
</script>
