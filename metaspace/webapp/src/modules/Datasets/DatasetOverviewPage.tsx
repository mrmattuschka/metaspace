import { computed, createComponent, ref } from '@vue/composition-api'
import { useQuery } from '@vue/apollo-composable'
import { GetDatasetByIdQuery, getDatasetByIdQuery } from '../../api/dataset'
import { Dropdown, DropdownItem, DropdownMenu } from 'element-ui'
import './DatasetOverviewPage.scss'

export default createComponent<{}>({
  setup(props, ctx) {

    const datasetId = computed(() => ctx.root.$route.params.datasetId)
    const {
      result: datasetResult,
      loading: datasetLoading,
    } = useQuery<GetDatasetByIdQuery>(getDatasetByIdQuery, {id: datasetId})
    const dataset = computed(() => datasetResult.value != null ? datasetResult.value.dataset : null)

    return () => dataset.value != null
      ? (
        <div class="dop--grid">
          <div class="dop--header">
            <div class="flex">
              <h1 class="flex-grow">{dataset.value != null ? dataset.value.name : null}</h1>
              <Dropdown class="dop--cog-menu">
                <i class="el-icon-s-tools dop--cog-menu--icon" />
                <DropdownMenu slot="dropdown">
                  <DropdownItem command="edit">Edit</DropdownItem>
                  <DropdownItem command="editOpt">Upload optical image</DropdownItem>
                  <DropdownItem command="download">Download</DropdownItem>
                  <DropdownItem command="reprocess">Reprocess</DropdownItem>
                  <DropdownItem command="delete">Delete</DropdownItem>
                </DropdownMenu>
              </Dropdown>
            </div>
          </div>
          <div class="dop--details">
            Details
          </div>
          <div class="dop--gallery">
            Gallery
          </div>
        </div>
      )
      : (
        <div class="loading">Loading</div>
      )
  },
})
