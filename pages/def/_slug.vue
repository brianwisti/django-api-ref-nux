<template>
  <div>
    <b-breadcrumb :items="breadcrumbs" />
    <h1>{{ functionDef.name }}</h1>
    <Docstring :docstring="functionDef.docstring" />
  </div>
</template>

<script>
export default {
  async asyncData({ $content, params }) {
    const functionDef = await $content('def', params.slug).fetch()
    let breadcrumbs = [];

    if (functionDef.package_name) {
      breadcrumbs.push({
        text: functionDef.package_name,
        href: `/pkg/${functionDef.package_name}`,
      })
    }
    else if (functionDef.module_name) {
      breadcrumbs.push({
        text: functionDef.module_name,
        href: `/mod/${functionDef.module_name}`,
      })
    }
    else if (functionDef.class_name) {
      breadcrumbs.push({
        text: functionDef.class_name,
        href: `/cls/${functionDef.class_name}`,
      })
    }

    breadcrumbs.push({
      text: functionDef.name,
      active: true
    });

    return {
      functionDef, breadcrumbs
    }
  }
}
</script>

