<template>
  <div>
    <b-breadcrumb :items="breadcrumbs" />
    <h1>Class {{ cls.name }}</h1>
    <Docstring :docstring="cls.docstring" />
    <FunctionList
      :functions="cls.methods"
      :parentName="cls.name"
      :isMethodList="true"
    />
  </div>
</template>

<script>
export default {
  async asyncData({ $content, params }) {
    const cls = await $content('cls', params.slug).fetch()
    let breadcrumbs = [];

    if (cls.package_name) {
      breadcrumbs.push({
        text: cls.package_name,
        href: `/pkg/${cls.package_name}`,
      })
    }
    else if (cls.module_name) {
      breadcrumbs.push({
        text: cls.module_name,
        href: `/mod/${cls.module_name}`,
      })
    }

    breadcrumbs.push({
      text: cls.name,
      active: true
    });

    return {
      cls, breadcrumbs
    }
  }
}
</script>
