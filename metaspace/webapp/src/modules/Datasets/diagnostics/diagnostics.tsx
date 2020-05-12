import Vue, { Component } from 'vue'
import { keyBy } from 'lodash-es'
import { createComponent } from '@vue/composition-api'
import ImageLoader from '../../../components/ImageLoader.vue'

interface DiagnosticInfo {
  id: string;
  name: string;
  helpText?: string;
  component: Component;
  previewComponent?: Component;
}

export const DIAGNOSTICS_LIST: DiagnosticInfo[] = [
  {
    id: 'ionPreview',
    name: 'Preview',
    component: createComponent({
      setup({data, ionImages}) {
        return () => <ImageLoader src={ionImages[0]} />
      },
    }),
  },
  {
    id: 'long',
    name: 'LongTextLongTextLongTextLongText LongTextLongTextLongTextLongText',
    component: createComponent({
      setup({data, ionImages}) {
        return () => <ImageLoader src={ionImages[0]} />
      },
    }),
  },
];

export const DIAGNOSTICS: Record<string, DiagnosticInfo> = keyBy(DIAGNOSTICS_LIST, 'id')
