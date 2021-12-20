<template>
  <div>
    <h2>Subpackages</h2>
    <div v-if="subpackages.length > 0">
      <div v-for="subpkg in subpackages" :key="subpkg.name">
        <PackageSummary :pkg="subpkg" />
      </div>
    </div>
    <b-alert show v-else>
      {{ packageName }} has no subpackages
    </b-alert>
  </div>
</template>

<script>
export default {
  name: "SubpackageList",
  props: {
    packageName: {
      type: String,
      required: true
    },
    subpackages: {
      type: Array,
      required: true
    }
  }
}
</script>
