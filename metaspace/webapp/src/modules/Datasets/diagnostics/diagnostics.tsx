import Vue, { Component, VueConstructor } from 'vue'
import { keyBy } from 'lodash-es'
import { createComponent } from '@vue/composition-api'
import ImageLoader from '../../../components/ImageLoader.vue'
import { ComponentOptions } from 'vue/types/options'

interface DiagnosticComponentProps {
  data: any;
  imageIds: string[];
}
type DiagnosticComponent = ComponentOptions<Vue, any, any, any, any, DiagnosticComponentProps> & {new(): any}
const diagnosticComponentProps = {
  data: { type: Object as () => any, required: true },
  imageIds: { type: Array as () => string[], required: true },
}

interface DiagnosticInfo {
  id: string;
  name: string;
  helpText?: string;
  component: DiagnosticComponent;
  previewComponent?: DiagnosticComponent;
}

export const DIAGNOSTICS_LIST: DiagnosticInfo[] = [
  {
    id: 'ionPreview',
    name: 'Preview',
    component: createComponent<DiagnosticComponentProps>({
      name: 'ionPreview',
      props: diagnosticComponentProps,
      setup({ imageIds }) {
        return () => <ImageLoader
          src={imageIds[0]}
          imagePosition={{ zoom: 1, xOffset: 0, yOffset: 0 }}
          minIntensity={0}
          maxIntensity={1}
          pixelAspectRatio={1}
        />
      },
    }),
  },
  {
    id: 'long',
    name: 'LongTextLongTextLongTextLongText LongTextLongTextLongTextLongText',
    component: createComponent<DiagnosticComponentProps>({
      props: diagnosticComponentProps,
      setup({ imageIds }) {
        return () => <ImageLoader
          src={imageIds[0]}
          imagePosition={{ zoom: 1, xOffset: 0, yOffset: 0 }}
        />
      },
    }),
  },
]

export const DIAGNOSTICS: Record<string, DiagnosticInfo> = keyBy(DIAGNOSTICS_LIST, 'id')
