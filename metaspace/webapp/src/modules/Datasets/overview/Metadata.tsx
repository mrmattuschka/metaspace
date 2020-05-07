import { createComponent } from '@vue/composition-api'
import { isArray, isPlainObject, range } from 'lodash-es'

interface Props {
  metadata: any
}

const Metadata = createComponent<Props>({
  name: 'Metadata',
  props: {
    metadata: Object as (() => any),
  },
  setup(props: Props) {
    const cleanString = (str: string) =>
      str.toString()
        .replace(/_/g, ' ')
        .replace(/ [A-Z][a-z]/g, (x) => ' ' + x.slice(1).toLowerCase())
        .replace(/ freetext$/, '')
        .replace(/ table$/, '')
    const newLinesToLineBreaks = (str: string) => {
      const parts = str.replace(/(\s*\n){2,}/g, '\n\n').split('\n')
      return range(parts.length * 2 - 1).map(i => i % 2 == 0 ? parts[i / 2] : <br />)
    }
    const customRenderers: Record<string, (val: any) => string | null> = {
      Detector_Resolving_Power: (rp: any) => {
        if (rp != null && rp.mz != null && rp.resolving_Power != null) {
          return `${(rp.Resolving_Power / 1000).toFixed(0)}k @ {rp.mz}`
        }
        return null
      },
      Pixel_Size: (pixelSize: any) => {
        if (pixelSize != null && pixelSize.Xaxis && pixelSize.Yaxis) {
          return `${pixelSize.Xaxis}μm × ${pixelSize.Yaxis}μm`
        }
        return null
      },
    }
    const cleanSectionContent = (content: any): string | [string, string][] => {
      if (isPlainObject(content)) {
        const entries = Object.entries(content)
        if (entries.length === 1 && entries[0][0] === 'Supplementary') {
          return entries[0][1] as string
        } else {
          return entries
            .map(([key, val]) =>
              [cleanString(key), key in customRenderers ? customRenderers[key](val) : val] as const)
            .filter(([key, val]) => val)
            .map(([key, val]) => [key, String(val)])
        }
      } else {
        return content as string
      }
    }
    return () => {
      const sections = Object.entries(props.metadata)
        .filter(([section]) => section != 'Data_Type')
        .map(([section, sectionContent]) => ([cleanString(section), cleanSectionContent(sectionContent)]))
      return (
        <div class="flex flex-wrap relative -m-3">
          {sections.map(([section, sectionContent]) => (
            <div key={section} class="m-3 flex-grow">
              <h4>{section}</h4>
              {isArray(sectionContent)
                ? <ul class="list-none pl-0">
                  {sectionContent.map(([key, value]) => value
                    ? <li key={key}><b>{key}:</b> {newLinesToLineBreaks(value)}</li>
                    : null)}
                </ul>
                : <p>{newLinesToLineBreaks(sectionContent)}</p>}
            </div>
          ))}
        </div>
      )
    }
  },
})

export default Metadata
