import { computed, createComponent, ref } from '@vue/composition-api'
import { RawLocation } from 'vue-router'
import { Button } from 'element-ui'
import Clickoutside from 'element-ui/lib/utils/clickoutside'
import FadeTransition from './FadeTransition'

interface Item {
  id: string
  text: string
  link?: RawLocation
  className?: string
  selected?: boolean
  onActivate?: (e: Event, id: string) => any
}

interface Props {
  icon?: string
  text?: string
  buttonType?: '' | 'primary' | 'text' // Or any other type accepted by ElButton
  chevron?: boolean
  align?: 'left' | 'center' | 'right'
  items: Item[]
}

/**
 * Alternative to ElementUI's ElDropdown that allows each item to have a `href` or `onClick`,
 * and synchronizes the width of the menu with the width of the trigger element.
 */
export default createComponent<Props>({

  directives: { Clickoutside },
  props: {
    icon: String,
    text: String,
    buttonType: String,
    chevron: {type: Boolean, default: false},
    align: {type: String, default: 'right'},
    items: Array,
  },
  setup(props, ctx) {
    const isOpen = ref(false);
    const toggle = () => { isOpen.value = !isOpen.value }
    const close = () => { isOpen.value = false }

    const items = computed(() => {
      const itemClass = 'block box-border w-full text-left px-4 py-2 text-sm leading-5 text-gray-700'
        + ' hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus:bg-gray-100 focus:text-gray-900'
      return props.items.map(item => {
        const onEvent = (e: MouseEvent | KeyboardEvent) => {
          if (item.onActivate != null
            && (e.type === 'click' || e.type === 'keyup' && (e as KeyboardEvent).key === 'Enter')) {
            item.onActivate(e, item.id)
            e.preventDefault()
            close()
          }
        }
        const commonProps = {
          key: item.id,
          class: [itemClass, item.className, {'': item.selected}],
          tabindex: 0,
          onClick: onEvent,
          onKeyup: onEvent,
        }

        if (item.link) {
          return (
            <router-link
              {...commonProps}
              to={item.link}>
              {item.text}
            </router-link>
          )
        } else {
          return (
            <span {...commonProps}>
              {item.text}
            </span>
          )
        }
      })
    })

    return () => {
      const originClass = {
        left: 'origin-top-left left-0',
        center: 'origin-top transform left-1/2 -translate-x-1/2', // transform has no IE11 support. positioning will be weird.
        right: 'origin-top-right right-0',
      }[props.align!]
      const buttonClass = props.buttonType === 'text'
      ? 'px-2 focus:border-blue-300 focus:shadow-outline-blue hover:border-blue-300 hover:shadow-outline-blue'
        : ''
      return (
        <div class="relative inline-block" v-clickoutside={close}>
          {ctx.slots.default != null
            ? ctx.slots.default()
            : <Button
              type={props.buttonType}
              class={buttonClass}
              icon={props.icon}
              onClick={toggle}>
              {props.text}
              {props.chevron && <i class="el-icon-arrow-down pl-2" />}
          </Button>}
          <FadeTransition>
            {isOpen.value
            && <div class={['absolute rounded-md shadow-lg min-w-full mt-2', originClass]}>
              <div class="rounded-md bg-white shadow-xs py-1">
                {items.value}
              </div>
            </div>}
          </FadeTransition>
        </div>
      )
    }
  }
})
