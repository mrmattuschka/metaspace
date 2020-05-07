import { createComponent } from '@vue/composition-api'
import { Dropdown, DropdownItem, DropdownMenu } from 'element-ui'

export const Menu = createComponent<{}>({
  setup() {
    return () => {
      return (
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
      )
    }
  },
})
