<template>
  <div>
    <h1>Class {{ cls.name }}</h1>
    <Docstring :docstring="cls.docstring" />
  </div>
</template>

<script>
export default {
  async asyncData({ $content, params }) {
    const cls = await $content('cls', params.slug).fetch()

    return {
      cls
    }
  }
}
</script>
