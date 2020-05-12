import { computed, createComponent, reactive, ref } from '@vue/composition-api'
import { useQuery } from '@vue/apollo-composable'
import safeJsonParse from '../../../lib/safeJsonParse'
import { GetDatasetByIdQuery, getDatasetByIdQuery } from '../../../api/dataset'
import { Menu } from './Menu'
import Metadata from './Metadata'
import { get, intersection, keyBy, range, zip } from 'lodash-es'
import { encodeParams } from '../../Filters'
import '../../../components/Table.scss'
import { Button } from 'element-ui'
import VisibilityBadge from '../common/VisibilityBadge'
import { DIAGNOSTICS } from '../diagnostics/diagnostics'
import DropdownMenu from '../../../components/DropdownMenu'

const annotationsLink = (datasetId: string, database?: string, fdrLevel?: number) => ({
  name: 'dataset-annotations',
  params: { datasetId },
  query: encodeParams({
    database,
    fdrLevel,
  }),
})

const AnnotationCounts = createComponent({
  name: 'AnnotationCounts',
  props: {
    datasetId: { type: String, required: true },
  },
  setup(props, ctx) {
    const fdrs = [5, 10, 20, 50]
    const dbCounts = [
      { database: 'HMDB-v4', counts: [1, 2, 3, 4] },
      { database: 'ChEBI', counts: [1, 2, 3, 4] },
    ]
    const totals = [2, 4, 5, 6]

    const countCell = (database?: string, fdr?: number, count?: number) => (
      <td class="text-center">
        <router-link to={annotationsLink(props.datasetId, database, fdr && fdr / 100)}>
          {count}
        </router-link>
      </td>
    )
    const browseAnnotations = () => {
      ctx.root.$router.push(annotationsLink(props.datasetId))
    }

    return () => {
      const tableClass = 'w-full sm-table sm-table-annotation-counts'
        + (dbCounts.length > 1 ? ' sm-table-annotation-counts--with-total' : '')
      return (
        <div class="relative max-w-measure-5">
          <table class={tableClass}>
            <colgroup>
              {range(1 + fdrs.length).map(() => <col width={`${1 / (1 + fdrs.length)}%`} />)}
            </colgroup>
            <tbody>
              <tr class="sm-table-header-row">
                <th />
                <th class="text-center" colspan={fdrs.length}>Molecules annotated with FDR &lt;=</th>
              </tr>
              <tr class="sm-table-header-row">
                <th />
                {fdrs.map(fdr => <th>{fdr}%</th>)}
              </tr>
              {dbCounts.map(({ database, counts }) => (
                <tr>
                  <th>{database}</th>
                  {zip(fdrs, counts).map(([fdr, count]) => countCell(database, fdr, count))}
                </tr>
              ))}
              {dbCounts.length > 1
              && <tr class="sm-table-total-row">
                <th>Total</th>
                {zip(fdrs, totals).map(([fdr, count]) => countCell('', fdr, count))}
              </tr>}
            </tbody>
          </table>
          <div class="text-right mt-2">
            <Button onClick={browseAnnotations}>Browse annotations</Button>
          </div>
        </div>
      )
    }
  },
})

export default createComponent<{}>({
  setup(props, ctx) {
    const { $router, $route } = ctx.root
    const datasetId = computed(() => $route.params.datasetId)
    const {
      result: datasetResult,
      loading: datasetLoading,
    } = useQuery<GetDatasetByIdQuery>(getDatasetByIdQuery, { id: datasetId })
    const dataset = computed(() => datasetResult.value != null ? datasetResult.value.dataset : null)
    const diagnosticData = reactive([
      {
        id: 'ionPreview',
        data: JSON.stringify({minIntensity: [0,0,1], maxIntensity: [3,4,5]}),
        images: [],
      },
      {
        id: 'long',
        data: JSON.stringify({minIntensity: [0,0,1], maxIntensity: [3,4,5]}),
        images: [],
      },
    ])
    const parsedDiagnostiData = diagnosticData.map(({data, ...rest}) => ({...rest, data: JSON.parse(data)}));
    const diagnosticDataLookup = reactive(keyBy(parsedDiagnostiData, 'id'))
    const selectedDiagId = ref<string>('ionPreview')
    const currentDiag = computed(() => DIAGNOSTICS[selectedDiagId.value] || null)
    const currentDiagData = computed(() => diagnosticDataLookup[selectedDiagId.value] || null)
    const availableDiagnosticIds = computed(() => intersection(Object.keys(DIAGNOSTICS), Object.keys(diagnosticDataLookup)))
    const availableDiagnostics = computed(() => availableDiagnosticIds.value.map(id => DIAGNOSTICS[id]))

    // const oldDropdown = () => (
    //   <Dropdown class="flex-grow text-center w-full">
    //     <div data-foo>
    //       {currentDiag.value != null ? currentDiag.value.name : selectedDiagId.value}
    //       <i class="el-icon-arrow-down px-3 foo" />
    //     </div>
    //
    //     <DropdownMenu>
    //       {availableDiagnostics.value.map(({id, name}) => (
    //         <DropdownItem command={id}>{name}</DropdownItem>
    //       ))}
    //
    //     </DropdownMenu>
    //   </Dropdown>
    // )

    return () => {
      if (datasetLoading.value && dataset.value == null) {
        return <div class="text-center">Loading...</div>
      } else if (dataset.value == null) {
        return <div class="text-center">This dataset doesn't exist, or you do not have access to it.</div>
      }
      const { name, submitter, group, principalInvestigator, isPublic, metadataJson } = dataset.value
      const metadata = safeJsonParse(metadataJson) || {}
      const groupLink = group && $router.resolve({ name: 'group', params: { groupIdOrSlug: group.id } }).href
      return (
        <div class="dop">
          <div class="dop--left">
            <div class="dop--header">
              <div class="flex items-center">
                <h1 class="truncate">{name}</h1>
                {!isPublic && <VisibilityBadge datasetId={datasetId.value} />}
                <div class="flex-grow" />
                <Menu />
              </div>
              <div>
                <b>Submitter: </b>
                <span>{submitter.name}</span>
                {group != null && <span> (<a href={groupLink}>{group.shortName}</a>)</span>}
              </div>
              {principalInvestigator != null
              && <div>
                <b>Principal Investigator: </b>
                <span>{principalInvestigator.name}</span>
              </div>}
            </div>
            <div class="dop--details">
              <h2>Annotations</h2>
              <AnnotationCounts datasetId={datasetId.value} />
              <h2>Details</h2>
              <Metadata metadata={metadata} />
            </div>
          </div>
          <div class="dop--right">
            <div class="dop--gallery">
              Gallery
              <div class="flex items-center justify-between">
                <i class="el-icon-s-grid invisible flex-none">{/*For centering the dropdown*/}</i>
                <div class="flex flex-grow items-center max-w-64">
                  <i class="el-icon-arrow-left" />
                  <DropdownMenu
                    text={currentDiag.value != null ? currentDiag.value.name : selectedDiagId.value}
                    buttonType="text"
                    align="center"
                    items={availableDiagnostics.value.map(({id, name}) => ({id, text: name, onClick: () => { selectedDiagId.value = id }}))}
                    chevron
                  />
                  <i class="el-icon-arrow-right" />
                </div>
                <i class="el-icon-s-grid" />
              </div>
            </div>
          </div>
        </div>
      )
    }
  },
})
