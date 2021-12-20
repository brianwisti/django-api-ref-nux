<template>
  <div>
    <b-breadcrumb :items="breadcrumbs" />
    <h1>Module {{ mod.namespace }}</h1>
    <Docstring :docstring="mod.docstring" />
    <b-container>
      <b-row>
        <b-col>
          <ClassList :classes="mod.classes" :parentName="mod.namespace" />
        </b-col>
        <b-col>
          <FunctionList
            :functions="mod.functions"
            :parentName="mod.namespace"
          />
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>

<script>
export default {
  async asyncData({ $content, params }) {
    const mod = await $content('mod', params.slug).fetch()

    let breadcrumbs = [];

    if (mod.package_name) {
      breadcrumbs.push({
        text: mod.package_name,
        href: `/pkg/${mod.package_name}`,
      })
    }

    breadcrumbs.push({
      text: mod.namespace,
      active: true
    });

    return {
      mod, breadcrumbs
    }
  }
}
</script>
