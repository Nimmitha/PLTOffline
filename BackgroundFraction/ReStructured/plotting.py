def plot_table(df, h):
    # print(df)
    with PdfPages(f"{IMG_PATH+str(h)}_plots.pdf") as pdf:
        for col in df.columns:
            print(col)
            plt.figure()
            plt.hist(df[col], bins=100, ls='solid', linewidth=3, edgecolor='k', alpha=.5, color='b')
            plt.title(col)
            # plt.show()
            plt.xlabel(col)
            plt.ylabel("No. of tracks")
            # plt.ylim([0, y_max*1.15])
            plt.grid()
            
            # y_max = max( max(outX[0]), max(outY[0]) )
            mean = df[col].mean()
            std = df[col].std()
            nfits = df.shape[0]

            textstr = f"fits\n{nfits:} fits\nMean: {mean:.2f}\nStd: {std:.2f}\n"
            plt.text(0.6, 0.8, textstr, transform=plt.gca().transAxes,
                    fontsize=24, verticalalignment='top', horizontalalignment='left',
                    bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))
            # hep.cms.label("Work in Progress", data=True, loc=1)
            # plt.savefig(f"{IMG_PATH+str(h)}_{col}.png")

            pdf.savefig()
            # pdf.savefig(fig)

    # save plots to pdf
    # with PdfPages(f"{IMG_PATH+str(h)}_plots.pdf") as pdf:
    #     for fig in range(1, plt.gcf().number + 1):
    #         pdf.savefig(fig)


        # plt.close()

        