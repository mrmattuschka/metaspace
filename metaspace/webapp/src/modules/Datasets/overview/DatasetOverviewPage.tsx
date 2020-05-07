import { computed, createComponent } from '@vue/composition-api'
import { useQuery } from '@vue/apollo-composable'
import safeJsonParse from '../../../lib/safeJsonParse'
import { GetDatasetByIdQuery, getDatasetByIdQuery } from '../../../api/dataset'
import { Menu } from './Menu'
import Metadata from './Metadata'

export default createComponent<{}>({
  setup(props, ctx) {
    const { $router, $route } = ctx.root
    const datasetId = computed(() => $route.params.datasetId)
    const {
      result: datasetResult,
      loading: datasetLoading,
    } = useQuery<GetDatasetByIdQuery>(getDatasetByIdQuery, { id: datasetId })
    const dataset = computed(() => datasetResult.value != null ? datasetResult.value.dataset : null)

    return () => {
      if (dataset.value == null) {
        return <div class="loading">Loading</div>
      }
      const { name, submitter, group, principalInvestigator, isPublic, metadataJson } = dataset.value;
      const metadata = safeJsonParse(metadataJson) || {};
      const groupLink = group && $router.resolve({ name: 'group', params: { groupIdOrSlug: group.id } }).href
      return (
        <div class="dop">
          <div class="dop--left">
            <div class="dop--header">
              <div class="flex">
                <h1 class="truncate">{name}</h1>
                {!isPublic && <i class="flex-none el-icon-s-tools" />}
                <div class="flex-grow" />
                <Menu />
              </div>
              <div>
                <b>Submitter: </b>
                <span>{submitter.name}</span>
                {group != null && <span> (<a href={groupLink}>{group.name}</a>)</span>}
              </div>
              {principalInvestigator != null
              && <div>
                  <b>Principal Investigator: </b>
                  <span>{principalInvestigator.name}</span>
                </div>}
            </div>
            <div class="dop--details">
              <h1>Annotations</h1>

              <h1>Details</h1>
              <Metadata metadata={metadata} />
            </div>
          </div>
          <div class="dop--right">
            <div class="dop--gallery">
              Gallery
            </div>
          </div>
        </div>
      )
    }
  },
})
