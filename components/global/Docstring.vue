<template>
  <b-card v-if="docstring.length > 0">
    <b-card-text>
      <pre>{{ docstring }}</pre>
    </b-card-text>
  </b-card>
</template>

<script>
export default {
  name: 'Docstring',
  props: {
    docstring: {
      type: String,
      required: true
    }
  }
}
</script>
