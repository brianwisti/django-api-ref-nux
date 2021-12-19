<template>
  <div>
    <h1>Package {{ pkg.name }}</h1>
    <b-card v-if="pkg.docstring.length > 0">
      <b-card-text>
        <pre>{{ pkg.docstring }}</pre>
      </b-card-text>
    </b-card>
    <b-container>
      <b-row>
        <b-col>
          <h2>Subpackages</h2>
          <div v-if="pkg.subpackages.length > 0">
            <div v-for="subpkg in pkg.subpackages" :key="subpkg.name">
              <NuxtLink :to="`/pkg/${subpkg.name}`">{{ subpkg.name }}</NuxtLink>
            </div>
          </div>
          <b-alert show v-else>
            {{ pkg.name }} has no subpackages
          </b-alert>
        </b-col>
        <b-col>
          <h2>Modules</h2>
          <div v-if="pkg.subpackages.length > 0">
            <div v-for="mod in pkg.modules" :key="mod.namespace">
              <NuxtLink :to="`/mod/${mod.namespace}`">{{ mod.namespace }}</NuxtLink>
            </div>
          </div>
          <b-alert show v-else>
            {{ pkg.name }} has no direct submodules.
          </b-alert>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>

<script>
export default {
  async asyncData({ $content, params }) {
    const pkg = await $content('pkg', params.slug).fetch()

    return {
      pkg
    }
  }
}
</script>
