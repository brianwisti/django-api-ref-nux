<template>
  <div>
    <b-breadcrumb :items="breadcrumbs" />
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
        <b-col>
          <ClassList
            :classes="pkg.classes"
            :parentName="pkg.name"
            />
        </b-col>
        <b-col>
          <FunctionList
            :functions="pkg.functions"
            :parentName="pkg.name"
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
    let breadcrumbs = [];

    if (pkg.package_name) {
      breadcrumbs.push({
        text: pkg.package_name,
        href: `/pkg/${pkg.package_name}`,
      })
    }

    breadcrumbs.push({
      text: pkg.name,
      active: true
    });

    return {
      pkg, breadcrumbs
    }
  }
}
</script>
