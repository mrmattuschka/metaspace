import { defineComponent, reactive } from '@vue/composition-api'
import { Option } from '../../lib/element-ui'
import './SortDropdown.css'
import { UnwrapRef } from '@vue/composition-api/dist/reactivity'

const enum SortingOrder {
  Unsorted = '',
  Asc = 'ASCENDING',
  Desc = 'DESCENDING',
}

interface Props {
  options: Option[]
  size: string
  onSortChange(value: any, orderBy: SortingOrder): any
}

interface State {
  value: any
  orderBy: SortingOrder
}

export const SortDropdown = defineComponent<Props>({
  props: {
    options: {
      type: Array,
      default: () => [
        {
          value: 'ORDER_BY_DATE',
          label: 'Last updated',
        },
        {
          value: 'ORDER_BY_UP_DATE',
          label: 'Upload date',
        },
        {
          value: 'ORDER_BY_NAME',
          label: 'Dataset name',
        },
        {
          value: 'ORDER_BY_DS_SUBMITTER_NAME',
          label: 'Submitter name',
        },
        {
          value: 'ORDER_BY_ANNOTATION_COUNTS',
          label: 'Annotation count',
        },
      ],
    },
    onSortChange: {
      type: Function,
      default: () => {},
    },
    size: {
      type: String,
      default: 'small',
    },
  },
  // Last reprocessed date (as currently)/Upload date/Number of annotations for FDR 10%/User name/Dataset name
  setup(props) {
    const state : UnwrapRef<State> = reactive({
      orderBy: SortingOrder.Unsorted,
      value: '',
    })

    const handleSort = () => {
      if (!state.value) { return null }

      state.orderBy = state.orderBy === SortingOrder.Unsorted ? SortingOrder.Desc : (state.orderBy === SortingOrder.Asc
        ? SortingOrder.Desc : SortingOrder.Asc)
      props.onSortChange(state.value, state.orderBy)
    }

    const handleSelect = (value: string) => {
      state.value = value
      state.orderBy = !value ? SortingOrder.Unsorted : (state.orderBy === SortingOrder.Unsorted
        ? SortingOrder.Desc : state.orderBy)
      props.onSortChange(state.value, state.orderBy)
    }

    return () => (
      <div class="flex flex-row sort-dp-container">
        <el-select size={props.size} value={state.value} placeholder="Sort by" onChange={handleSelect} clearable>
          {
            props.options.map((opt) => {
              return <el-option
                label={opt.label}
                value={opt.value}/>
            })
          }
        </el-select>
        <div class="el-input-group__append sort-dp-btn">
          <el-tooltip
            content="Sorting order"
            placement="right"
          >
            <el-button
              class={`${!state.value ? 'cursor-not-allowed' : ''}`}
              icon={state.orderBy === SortingOrder.Unsorted ? 'el-icon-sort' : (state.orderBy === SortingOrder.Desc
                ? 'el-icon-sort-down' : 'el-icon-sort-up')}
              onClick={handleSort}
            />
          </el-tooltip>
        </div>
      </div>
    )
  },
})
