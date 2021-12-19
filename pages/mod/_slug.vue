<template>
  <div>
    <h1>Module {{ mod.namespace }}</h1>
    <b-card v-if="mod.docstring.length > 0">
      <b-card-text>
        <pre>{{ mod.docstring }}</pre>
      </b-card-text>
    </b-card>
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
