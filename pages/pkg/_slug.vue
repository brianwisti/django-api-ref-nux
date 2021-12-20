<template>
  <div>
    <h1>Package {{ pkg.name }}</h1>
    <Docstring :docstring="pkg.docstring" />
    <b-container>
      <b-row>
        <b-col>
          <SubpackageList
            :subpackages="pkg.subpackages"
            :packageName="pkg.name"
            />
        </b-col>
        <b-col>
          <ModuleList
            :modules="pkg.modules"
            :packageName="pkg.name"
            />
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
