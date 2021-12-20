<template>
  <div>
    <h1>Module {{ mod.namespace }}</h1>
    <Docstring :docstring="mod.docstring" />
    <ClassList :classes="mod.classes" :parentName="mod.namespace" />
  </div>
</template>

<script>
export default {
  async asyncData({ $content, params }) {
    const mod = await $content('mod', params.slug).fetch()

    return {
      mod
    }
  }
}
</script>
